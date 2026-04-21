import { useState, useEffect } from 'react';
import { useVoice } from './hooks/useVoice';
import { StateList } from './components/StateList';
import { Cart } from './components/Cart';
import { MessageSquare } from 'lucide-react';


function App() {
  const {
    isListening,
    transcript,
    startListening,
    stopListening,
    lastResult,
    forceSetState,
    currentStateId,
    processText
  } = useVoice("demo-user");

  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Trigger refresh when lastResult changes (implying a backend operation happened)
  useEffect(() => {
    setRefreshTrigger(prev => prev + 1);
  }, [lastResult]);

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-4">
      <StateList
        userId="demo-user"
        onResume={forceSetState}
        activeStateId={currentStateId}
        refreshTrigger={refreshTrigger}
      />

      <div className="w-full max-w-2xl space-y-8">
        {/* Dynamic header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm mb-4">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
            </span>
            VPOS AI System
          </div>
          <h1 className="text-5xl font-bold tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
            Voice Point of Sale
          </h1>
          <p className="text-gray-400 text-lg">
            "Vende 2 cocas" • "¿Cuánto cuesta el jabón?" • "Inventario"
          </p>
        </div>

        {/* Main Interface Block */}
        <div className="bg-gray-900/50 border border-white/10 rounded-2xl p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden">
          {/* Gradient glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent opacity-50"></div>

          {/* Result Area */}
          <div className="mb-8 min-h-[120px] flex flex-col items-center justify-center text-center">

            {/* 1. Explicit Recognized Command Banner */}
            {transcript && (
              <div className="mb-4 px-4 py-2 bg-blue-900/40 border border-blue-500/30 rounded-lg flex items-center gap-2 animate-in fade-in slide-in-from-top-2">
                <MessageSquare className="w-4 h-4 text-blue-400" />
                <span className="text-blue-200 text-sm font-light">
                  Escuchado: <span className="font-bold text-white italic">"{transcript}"</span>
                </span>
              </div>
            )}

            {lastResult ? (
              <div className="space-y-3 animate-in fade-in slide-in-from-bottom-4 duration-500">
                {lastResult.action === "AMBIGUITY_DETECTED" && (
                  <div className="text-yellow-400 font-medium mb-2 text-sm tracking-wide uppercase">⚡ Ambigüedad Detectada</div>
                )}
                {lastResult.action === "COMPLETED" && (
                  <div className="text-green-400 font-medium mb-2 text-sm tracking-wide uppercase">✓ Completado</div>
                )}
                {lastResult.action === "INFO" && (
                  <div className="text-blue-400 font-medium mb-2 text-sm tracking-wide uppercase">ℹ️ Info</div>
                )}
                {lastResult.action === "STATE_UPDATE" && !lastResult.missing_fields?.length && (
                  <div className="text-blue-500 font-bold mb-2 text-sm tracking-wide uppercase animate-bounce">🚀 Listo para Confirmar</div>
                )}
                {lastResult.action === "STATE_UPDATE" && lastResult.missing_fields?.length > 0 && (
                  <div className="text-yellow-500/80 font-medium mb-2 text-sm tracking-wide uppercase">📝 Recolectando Datos</div>
                )}

                <div className="text-2xl font-light leading-relaxed">
                  {lastResult.message}
                </div>

                {/* Progress / Missing Fields Visualization */}
                {lastResult.missing_fields && lastResult.missing_fields.length > 0 && (
                  <div className="mt-6 border-t border-white/10 pt-4">
                    <div className="text-xs uppercase tracking-widest text-gray-400 mb-3 font-semibold text-left ml-1">
                      Completando Información:
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {/* Show collected data as completed chips */}
                      {lastResult.data && Object.entries(lastResult.data).map(([key, value]) => {
                        if (key.startsWith('_')) return null; // Skip internal flags
                        return (
                          <div key={key} className="px-3 py-1.5 rounded-lg bg-green-500/20 border border-green-500/30 text-green-300 text-sm flex items-center gap-2">
                            <span className="opacity-70 text-xs uppercase">{key}:</span>
                            <span className="font-semibold">{String(value)}</span>
                            <span className="text-green-500">✓</span>
                          </div>
                        );
                      })}

                      {/* Show missing fields as pending chips */}
                      {Array.isArray(lastResult.missing_fields) && lastResult.missing_fields.map((field: string) => (
                        <div key={field} className="px-3 py-1.5 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-yellow-500/80 text-sm flex items-center gap-2 animate-pulse">
                          <span className="font-semibold capitalize">{field}</span>
                          <span className="text-yellow-500 font-bold">?</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Cart Display */}
                <Cart
                  cart={lastResult?.data?.cart || []}
                  total={lastResult?.data?.total || 0}
                  onRemoveItem={(productName) => processText(`borrar ${productName}`)}
                />

                {/* Data Payload Visualization (Hidden if Cart active to reduce noise) */}
                {lastResult.data && !lastResult.data.cart && (
                  <div className="mt-4 p-4 bg-black/40 rounded-lg border border-white/5 text-left font-mono text-sm text-blue-200/80 overflow-x-auto">
                    <pre>{JSON.stringify(lastResult.data, null, 2)}</pre>
                  </div>
                )}

                {/* Ambiguity Candidates */}
                {lastResult.candidates && (
                  <div className="flex gap-2 justify-center flex-wrap mt-4">
                    {lastResult.candidates.map((c: any) => (
                      <button
                        key={c.id}
                        onClick={() => processText(c.nombre)} // Click to select automatically
                        className="px-4 py-2 bg-blue-600/20 hover:bg-blue-600/40 rounded-full text-sm transition-all border border-blue-500/30 text-blue-300 font-medium"
                      >
                        {c.nombre}
                      </button>
                    ))}
                  </div>
                )}

                {/* Direct Action Buttons (Confirm/Cancel) when ready */}
                {lastResult.action === "STATE_UPDATE" && !lastResult.missing_fields?.length && (
                  <div className="flex gap-4 justify-center mt-6">
                    <button
                      onClick={() => processText("sí")}
                      className="px-8 py-3 bg-green-600 hover:bg-green-500 rounded-xl text-white font-bold transition-all shadow-[0_0_20px_rgba(22,163,74,0.4)] flex items-center gap-2"
                    >
                      <span>Confirmar Venta</span>
                      <span className="text-xl">✓</span>
                    </button>
                    <button
                      onClick={() => processText("cancelar")}
                      className="px-8 py-3 bg-gray-800 hover:bg-gray-700 rounded-xl text-gray-300 font-medium transition-all border border-white/5"
                    >
                      Cancelar
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-gray-500 font-light italic">
                Esperando comando...
              </div>
            )}
          </div>

          {/* Transcript Area */}
          <div className={`transition - all duration - 300 ${isListening ? 'opacity-100 scale-100' : 'opacity-50 scale-95'} `}>
            <div className="text-center">
              <div className="text-sm uppercase tracking-widest text-gray-500 mb-2 font-medium">Transcript</div>
              <div className="text-xl text-white font-medium min-h-[1.5em]">
                {transcript || "..."}
              </div>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-col items-center gap-6">
          <button
            onClick={isListening ? stopListening : startListening}
            className={`
                group relative flex items - center justify - center w - 20 h - 20 rounded - full transition - all duration - 300
                ${isListening
                ? 'bg-red-500/20 hover:bg-red-500/30 border-red-500/50'
                : 'bg-blue-600 hover:bg-blue-500 border-blue-400/50 shadow-[0_0_30px_-5px_rgba(37,99,235,0.5)]'
              }
border - 2 backdrop - blur - sm
  `}
          >
            {isListening ? (
              <div className="w-6 h-6 bg-red-500 rounded-sm shadow-[0_0_15px_rgba(239,68,68,0.6)] animate-pulse" />
            ) : (
              <svg className="w-8 h-8 text-white drop-shadow-md" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            )}
          </button>

          {/* Text Input Option */}
          <div className="w-full max-w-md relative flex items-center">
            <input
              type="text"
              placeholder="O escribe tu comando aquí..."
              className="w-full bg-gray-900/50 border border-gray-700 text-white rounded-full py-3 px-6 pr-12 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-gray-600"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const target = e.target as HTMLInputElement;
                  if (target.value.trim()) {
                    processText(target.value);
                    target.value = '';
                  }
                }
              }}
            />
            <button
              className="absolute right-2 p-2 bg-blue-600 rounded-full hover:bg-blue-500 text-white transition-colors"
              onClick={(e) => {
                const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                if (input.value.trim()) {
                  processText(input.value);
                  input.value = '';
                }
              }}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </div>
        </div>

        <p className="text-center text-xs text-gray-600 mt-8">
          Pulsa el micrófono para hablar o escribir un comando. Comandos válidos: "Vende...", "Buscar...", "Cancelar"
        </p>
      </div>
    </div>
  );
}

export default App;
