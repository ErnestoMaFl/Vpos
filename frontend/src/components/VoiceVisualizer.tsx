import React from 'react';
import { cn } from '../lib/utils';

interface VoiceVisualizerProps {
    isListening: boolean;
    volume: number; // 0 to 1
}

export const VoiceVisualizer: React.FC<VoiceVisualizerProps> = ({ isListening, volume }) => {
    return (
        <div className="flex items-center justify-center gap-1 h-12">
            {[...Array(5)].map((_, i) => (
                <div
                    key={i}
                    className={cn(
                        "w-2 bg-primary rounded-full transition-all duration-100 ease-in-out",
                        isListening ? "animate-pulse" : "h-2 opacity-50"
                    )}
                    style={{
                        height: isListening ? `${Math.max(20, volume * 100 * (1 + Math.sin(i)))}%` : '8px'
                    }}
                />
            ))}
        </div>
    );
};
