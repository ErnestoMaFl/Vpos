import { Activity, ShoppingCart, User } from 'lucide-react';
import { cn } from '../lib/utils';

interface StateDisplayProps {
    lastResult: any;
}

export const StateDisplay = ({ lastResult }: StateDisplayProps) => {
    if (!lastResult) return null;

    const { action, intent, table, data, message, details } = lastResult;

    // Determine Icon based on table or intent
    const getIcon = () => {
        if (table === 'ventas') return <ShoppingCart className="h-6 w-6" />;
        if (table === 'clients') return <User className="h-6 w-6" />;
        return <Activity className="h-6 w-6" />;
    };

    const getStatusColor = () => {
        if (action === 'UNKNOWN') return 'border-yellow-500/50 bg-yellow-500/10 text-yellow-500';
        if (action === 'CANCEL_STATE') return 'border-red-500/50 bg-red-500/10 text-red-500';
        return 'border-blue-500/50 bg-blue-500/10 text-blue-500';
    };

    return (
        <div className={cn("w-full transition-all duration-500 ease-out transform",
            lastResult ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
        )}>
            <div className={cn("rounded-xl border p-4 flex items-start gap-4 backdrop-blur-sm", getStatusColor())}>
                <div className="p-2 rounded-lg bg-background/50">
                    {getIcon()}
                </div>

                <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-lg tracking-tight uppercase opacity-90">
                            {intent || action || "Estado"}
                        </h3>
                        <span className="text-xs font-mono opacity-70 px-2 py-1 rounded bg-background/30">
                            {table || "System"}
                        </span>
                    </div>

                    <p className="text-sm opacity-90 font-medium">
                        {message || "Procesando comando..."}
                    </p>

                    {/* Data Grid for parameters */}
                    {data && (
                        <div className="grid grid-cols-2 gap-2 mt-3 p-2 bg-background/20 rounded-lg">
                            {Object.entries(data).map(([key, value]) => (
                                <div key={key} className="flex flex-col">
                                    <span className="text-[10px] uppercase opacity-70">{key}</span>
                                    <span className="font-mono text-sm font-bold truncate">{String(value)}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Debug/Details View */}
                    {details && (
                        <div className="mt-2 text-xs opacity-60 font-mono">
                            {JSON.stringify(details)}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
