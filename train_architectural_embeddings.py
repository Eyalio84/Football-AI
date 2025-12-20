#!/usr/bin/env python3
"""
Architectural KG Embeddings Trainer

Trains self-supervised contextual embeddings for the Soccer-AI architectural KG.
Uses graph structure and text content (no external models required).

Training Strategy:
1. Token-level embeddings (256-dim) from node names/descriptions
2. Context aggregation via graph neighbors
3. Contrastive learning (connected nodes = similar, random = dissimilar)
4. Output: embeddings.npz for semantic search (numpy format - safe)

Based on NLKE v3.0 methodology: Structure > Training
"""

import sqlite3
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict, Counter
import re

# Paths
BASE_DIR = Path(__file__).parent
KG_DB = BASE_DIR / "soccer_ai_architecture_kg.db"
OUTPUT_FILE = BASE_DIR / "architectural_embeddings.npz"  # Safe numpy format

# Hyperparameters
EMBEDDING_DIM = 256
LEARNING_RATE = 0.01
EPOCHS = 50
NEGATIVE_SAMPLES = 5
TEMPERATURE = 0.1


class TokenEmbedder:
    """Simple token-level embedder using character n-grams and word hashing"""

    def __init__(self, embedding_dim: int = 256):
        self.embedding_dim = embedding_dim
        self.vocab = {}
        self.vocab_size = 0

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words and character n-grams"""
        text = text.lower()
        # Word-level tokens
        words = re.findall(r'\w+', text)
        # Character 3-grams for subword information
        char_ngrams = []
        for word in words:
            word = f"<{word}>"
            for i in range(len(word) - 2):
                char_ngrams.append(word[i:i+3])
        return words + char_ngrams

    def build_vocab(self, texts: List[str], min_freq: int = 2):
        """Build vocabulary from texts"""
        token_counts = Counter()
        for text in texts:
            tokens = self.tokenize(text)
            token_counts.update(tokens)

        # Keep tokens with frequency >= min_freq
        self.vocab = {
            token: idx
            for idx, (token, count) in enumerate(token_counts.items())
            if count >= min_freq
        }
        self.vocab_size = len(self.vocab)
        print(f"Vocabulary size: {self.vocab_size}")

    def embed(self, text: str) -> np.ndarray:
        """Embed text as sum of token vectors"""
        tokens = self.tokenize(text)
        embedding = np.zeros(self.embedding_dim)

        for token in tokens:
            if token in self.vocab:
                # Simple hash-based embedding
                token_idx = self.vocab[token]
                # Use deterministic random vector for this token
                np.random.seed(token_idx)
                token_vec = np.random.randn(self.embedding_dim)
                token_vec /= np.linalg.norm(token_vec)
                embedding += token_vec

        # Normalize
        if np.linalg.norm(embedding) > 0:
            embedding /= np.linalg.norm(embedding)

        return embedding


class GraphContextualizer:
    """Contextualizes embeddings using graph structure"""

    def __init__(self, kg_db_path: Path):
        self.kg_db_path = kg_db_path
        self.nodes = {}  # node_id -> node_data
        self.edges = defaultdict(list)  # node_id -> [neighbor_ids]
        self.edge_types = {}  # (from, to) -> relationship
        self.load_graph()

    def load_graph(self):
        """Load graph structure from database"""
        conn = sqlite3.connect(self.kg_db_path)
        cursor = conn.cursor()

        # Load nodes
        cursor.execute("SELECT node_id, name, type, description, properties FROM kg_nodes")
        for row in cursor.fetchall():
            node_id, name, ntype, description, properties = row
            self.nodes[node_id] = {
                "name": name,
                "type": ntype,
                "description": description or "",
                "properties": json.loads(properties) if properties else {}
            }

        # Load edges
        cursor.execute("SELECT from_node, to_node, relationship, weight FROM kg_edges")
        for row in cursor.fetchall():
            from_node, to_node, relationship, weight = row
            self.edges[from_node].append(to_node)
            self.edges[to_node].append(from_node)  # Bidirectional
            self.edge_types[(from_node, to_node)] = relationship

        conn.close()

        print(f"Loaded {len(self.nodes)} nodes, {len(self.edge_types)} edges")

    def get_neighbor_context(self, node_id: int, embeddings: Dict[int, np.ndarray]) -> np.ndarray:
        """Aggregate embeddings of neighbors"""
        neighbors = self.edges.get(node_id, [])

        if not neighbors:
            return np.zeros(embeddings[node_id].shape)

        # Weighted average of neighbor embeddings
        context = np.zeros(embeddings[node_id].shape)
        for neighbor_id in neighbors:
            if neighbor_id in embeddings:
                # Weight by relationship type (some relationships are more important)
                rel = self.edge_types.get((node_id, neighbor_id)) or self.edge_types.get((neighbor_id, node_id))
                weight = 1.0
                if rel in ["uses", "queries", "traverses", "exposes"]:
                    weight = 1.5  # More important relationships
                context += embeddings[neighbor_id] * weight

        # Normalize
        if np.linalg.norm(context) > 0:
            context /= np.linalg.norm(context)

        return context

    def get_text(self, node_id: int) -> str:
        """Get concatenated text for a node"""
        node = self.nodes[node_id]
        parts = [
            node["name"],
            node["type"],
            node["description"]
        ]

        # Add key properties
        props = node.get("properties", {})
        if "path" in props:
            parts.append(props["path"])
        if "method" in props:
            parts.append(props["method"])
        if "table_name" in props:
            parts.append(props["table_name"])
        if "club_key" in props:
            parts.append(props["club_key"])

        return " ".join(str(p) for p in parts if p)


class ContrastiveLearner:
    """Trains embeddings using contrastive learning"""

    def __init__(self, contextualizer: GraphContextualizer, embedder: TokenEmbedder):
        self.contextualizer = contextualizer
        self.embedder = embedder
        self.embeddings = {}
        self.initialize_embeddings()

    def initialize_embeddings(self):
        """Initialize embeddings from text"""
        print("Initializing embeddings from text...")
        for node_id in self.contextualizer.nodes:
            text = self.contextualizer.get_text(node_id)
            self.embeddings[node_id] = self.embedder.embed(text)
        print(f"Initialized {len(self.embeddings)} node embeddings")

    def contrastive_loss(self, anchor: np.ndarray, positive: np.ndarray,
                        negatives: List[np.ndarray], temperature: float = 0.1) -> float:
        """InfoNCE contrastive loss"""
        # Similarity scores
        pos_sim = np.dot(anchor, positive) / temperature
        neg_sims = [np.dot(anchor, neg) / temperature for neg in negatives]

        # Log-sum-exp trick for numerical stability
        max_sim = max(pos_sim, max(neg_sims))
        pos_exp = np.exp(pos_sim - max_sim)
        neg_exp_sum = sum(np.exp(sim - max_sim) for sim in neg_sims)

        loss = -np.log(pos_exp / (pos_exp + neg_exp_sum))
        return loss

    def train(self, epochs: int = 50, lr: float = 0.01, neg_samples: int = 5):
        """Train embeddings using contrastive learning"""
        print(f"Training for {epochs} epochs...")

        node_ids = list(self.contextualizer.nodes.keys())
        losses = []

        for epoch in range(epochs):
            epoch_loss = 0.0
            num_updates = 0

            # Shuffle nodes
            np.random.shuffle(node_ids)

            for anchor_id in node_ids:
                # Get positive sample (neighbor)
                neighbors = self.contextualizer.edges.get(anchor_id, [])
                if not neighbors:
                    continue

                positive_id = np.random.choice(neighbors)

                # Get negative samples (random non-neighbors)
                non_neighbors = [nid for nid in node_ids if nid != anchor_id and nid not in neighbors]
                if len(non_neighbors) < neg_samples:
                    continue

                negative_ids = np.random.choice(non_neighbors, size=neg_samples, replace=False)

                # Compute loss
                anchor_emb = self.embeddings[anchor_id]
                positive_emb = self.embeddings[positive_id]
                negative_embs = [self.embeddings[nid] for nid in negative_ids]

                loss = self.contrastive_loss(anchor_emb, positive_emb, negative_embs, TEMPERATURE)
                epoch_loss += loss
                num_updates += 1

                # Gradient update (simplified - push apart from negatives, pull together with positive)
                # Positive gradient
                pos_gradient = positive_emb - anchor_emb
                self.embeddings[anchor_id] += lr * pos_gradient

                # Negative gradients
                for neg_emb in negative_embs:
                    neg_gradient = anchor_emb - neg_emb
                    self.embeddings[anchor_id] += lr * neg_gradient * 0.5

                # Normalize
                self.embeddings[anchor_id] /= np.linalg.norm(self.embeddings[anchor_id])

            avg_loss = epoch_loss / num_updates if num_updates > 0 else 0.0
            losses.append(avg_loss)

            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

        return losses

    def contextualize(self, alpha: float = 0.7):
        """Mix text embeddings with graph context"""
        print("Contextualizing embeddings with graph structure...")

        contextualized = {}
        for node_id in self.embeddings:
            text_emb = self.embeddings[node_id].copy()
            context_emb = self.contextualizer.get_neighbor_context(node_id, self.embeddings)

            # Weighted combination
            final_emb = alpha * text_emb + (1 - alpha) * context_emb

            # Normalize
            if np.linalg.norm(final_emb) > 0:
                final_emb /= np.linalg.norm(final_emb)

            contextualized[node_id] = final_emb

        self.embeddings = contextualized

    def save(self, output_path: Path):
        """Save embeddings to numpy npz file (safe format)"""
        print(f"Saving embeddings to {output_path}...")

        # Convert dict to arrays
        node_ids = list(self.embeddings.keys())
        embeddings_matrix = np.array([self.embeddings[nid] for nid in node_ids])

        # Prepare metadata
        node_names = [self.contextualizer.nodes[nid]["name"] for nid in node_ids]
        node_types = [self.contextualizer.nodes[nid]["type"] for nid in node_ids]

        # Save to npz (compressed numpy format - safe and efficient)
        np.savez_compressed(
            output_path,
            node_ids=np.array(node_ids),
            embeddings=embeddings_matrix,
            node_names=np.array(node_names),
            node_types=np.array(node_types),
            dimension=EMBEDDING_DIM,
            epochs=EPOCHS,
            method="contrastive_learning"
        )

        print(f"Saved embeddings for {len(self.embeddings)} nodes")
        print(f"File size: {output_path.stat().st_size / 1024:.2f} KB")


def main():
    """Main training pipeline"""
    print("="*60)
    print("Architectural KG Embeddings Trainer")
    print("="*60)
    print()

    # 1. Load graph
    print("Step 1: Loading graph structure...")
    contextualizer = GraphContextualizer(KG_DB)
    print()

    # 2. Build vocabulary
    print("Step 2: Building vocabulary...")
    embedder = TokenEmbedder(EMBEDDING_DIM)
    texts = [contextualizer.get_text(node_id) for node_id in contextualizer.nodes]
    embedder.build_vocab(texts, min_freq=1)
    print()

    # 3. Train embeddings
    print("Step 3: Training embeddings...")
    learner = ContrastiveLearner(contextualizer, embedder)
    losses = learner.train(epochs=EPOCHS, lr=LEARNING_RATE, neg_samples=NEGATIVE_SAMPLES)
    print()

    # 4. Contextualize with graph
    print("Step 4: Contextualizing with graph...")
    learner.contextualize(alpha=0.7)
    print()

    # 5. Save
    print("Step 5: Saving embeddings...")
    learner.save(OUTPUT_FILE)
    print()

    print("="*60)
    print("✓ Training complete!")
    print(f"✓ Output: {OUTPUT_FILE}")
    print("="*60)


if __name__ == "__main__":
    main()
