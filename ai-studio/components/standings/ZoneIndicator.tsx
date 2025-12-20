import React from 'react';

interface ZoneIndicatorProps {
  position: number;
}

export const ZoneIndicator: React.FC<ZoneIndicatorProps> = ({ position }) => {
  let colorClass = '';

  if (position <= 4) colorClass = 'bg-blue-500'; // Champions League
  else if (position <= 6) colorClass = 'bg-orange-500'; // Europa League
  else if (position === 7) colorClass = 'bg-emerald-500'; // Conference
  else if (position >= 18) colorClass = 'bg-red-600'; // Relegation
  else return null;

  return (
    <div className={`absolute left-0 top-0 bottom-0 w-1 ${colorClass}`} />
  );
};