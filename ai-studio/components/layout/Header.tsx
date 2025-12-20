import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useClub } from '../../hooks/useClub';
import { ClubSelector } from '../chat/ClubSelector';

export const Header: React.FC = () => {
  const { clubColors, clubName } = useClub();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Chat' },
    { path: '/standings', label: 'Table' },
    { path: '/fixtures', label: 'Fixtures' },
    { path: '/predictions', label: 'Predictions' },
  ];

  return (
    <header className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-lg border-b border-slate-700/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Branding */}
          <div className="flex items-center gap-3">
            <div 
              className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-white shadow-lg transition-colors duration-300"
              style={{ backgroundColor: clubColors.primary }}
            >
              AI
            </div>
            <div className="hidden md:block">
              <h1 className="text-lg font-bold text-white leading-none">Soccer-AI</h1>
              <p className="text-xs text-slate-400 font-medium">Fan at heart.</p>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-1">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                    isActive 
                      ? 'text-white bg-slate-800 shadow-sm' 
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                  }`
                }
                style={({ isActive }) => isActive ? { borderBottom: `2px solid ${clubColors.primary}` } : {}}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          {/* Club Selector & Mobile Menu Button */}
          <div className="flex items-center gap-4">
            <ClubSelector />
            
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="md:hidden p-2 rounded-md text-slate-400 hover:text-white hover:bg-slate-800"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {isMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isMenuOpen && (
        <div className="md:hidden bg-slate-800 border-b border-slate-700/50">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setIsMenuOpen(false)}
                className={({ isActive }) =>
                  `block px-3 py-2 rounded-md text-base font-medium ${
                    isActive ? 'text-white bg-slate-700' : 'text-slate-400 hover:text-white hover:bg-slate-700'
                  }`
                }
                style={({ isActive }) => isActive ? { color: clubColors.primary } : {}}
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        </div>
      )}
    </header>
  );
};