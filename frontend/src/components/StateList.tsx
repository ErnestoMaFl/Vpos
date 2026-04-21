import { useState, useEffect } from 'react';

interface State {
    id: string;
    command_origin: string;
    timestamp_creacion: string;
    valor_retorno_esperado: string;
    datos_recolectados: any;
}

interface StateListProps {
    userId: string;
    onResume: (stateId: string) => void;
    activeStateId?: string | null;
    refreshTrigger: number; // Increment to force refresh
}

export const StateList = ({ userId, onResume, activeStateId, refreshTrigger }: StateListProps) => {
    const [states, setStates] = useState<State[]>([]);
    const [isOpen, setIsOpen] = useState(true);

    useEffect(() => {
        fetch(`http://localhost:8000/api/states/${userId}`)
            .then(res => {
                if (!res.ok) throw new Error("Failed to fetch states");
                return res.json();
            })
            .then(data => setStates(data.states || []))
            .catch(err => {
                console.error("Error fetching states:", err);
                setStates([]);
            });
    }, [userId, refreshTrigger]);

    if (!states.length) return null;

    return (
        <div className="fixed top-4 right-4 w-64 bg-gray-900 border border-gray-700 rounded-lg shadow-xl overflow-hidden z-50">
            <div
                className="bg-gray-800 px-4 py-2 flex justify-between items-center cursor-pointer"
                onClick={() => setIsOpen(!isOpen)}
            >
                <h3 className="text-sm font-semibold text-gray-200">Active Processes ({states.length})</h3>
                <span className="text-gray-400">{isOpen ? '▼' : '▶'}</span>
            </div>

            {isOpen && (
                <div className="max-h-96 overflow-y-auto">
                    {states.map(state => {
                        const isActive = state.id === activeStateId;
                        const contextName = state.valor_retorno_esperado?.replace("campos_para_", "") || "General";

                        return (
                            <div
                                key={state.id}
                                className={`p-3 border-b border-gray-800 ${isActive ? 'bg-blue-900/20 border-l-2 border-l-blue-500' : 'hover:bg-gray-800'}`}
                            >
                                <div className="text-xs text-blue-400 mb-1 uppercase tracking-wider font-bold">
                                    {contextName}
                                </div>
                                <div className="text-sm text-gray-300 font-medium mb-1 truncate" title={state.command_origin}>
                                    "{state.command_origin}"
                                </div>
                                <div className="text-xs text-gray-500 mb-2">
                                    {new Date(state.timestamp_creacion).toLocaleTimeString()}
                                </div>

                                {isActive ? (
                                    <span className="text-xs text-green-400 font-mono">● Active Context</span>
                                ) : (
                                    <button
                                        onClick={() => onResume(state.id)}
                                        className="w-full py-1 px-2 bg-gray-700 hover:bg-gray-600 text-xs text-gray-200 rounded transition-colors"
                                    >
                                        Resume / Switch To
                                    </button>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};
