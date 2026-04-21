import React from 'react';

interface CartItem {
    producto_id: number;
    nombre_producto: string;
    cantidad: number;
    precio_unitario: number;
    subtotal: number;
}


interface CartProps {
    cart: CartItem[];
    total: number;
    onRemoveItem?: (productName: string) => void;
}

export const Cart: React.FC<CartProps> = ({ cart, total, onRemoveItem }) => {
    if (!cart) return null;

    return (
        <div className="w-full max-w-md mx-auto bg-gray-900 border border-white/10 rounded-xl overflow-hidden shadow-2xl mt-6">
            <div className="bg-gray-800/50 p-4 border-b border-white/5 flex justify-between items-center">
                <h3 className="text-gray-200 font-semibold tracking-wide flex items-center gap-2">
                    🛒 Carrito de Venta
                </h3>
                <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full border border-blue-500/30">
                    {cart.length} items
                </span>
            </div>

            <div className="divide-y divide-white/5 max-h-60 overflow-y-auto min-h-[100px]">
                {cart.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-24 text-gray-500 text-sm italic">
                        <span>Tu carrito está vacío</span>
                        <span className="text-xs opacity-50 mt-1">Di "Agregar [producto]"</span>
                    </div>
                )}
                {cart.map((item, idx) => (
                    <div key={idx} className="p-4 flex justify-between items-start hover:bg-white/5 transition-colors group">
                        <div>
                            <div className="text-white font-medium">{item.nombre_producto}</div>
                            <div className="text-sm text-gray-400">
                                {item.cantidad} x ${item.precio_unitario}
                            </div>
                        </div>
                        <div className="text-right flex items-center gap-3">
                            <div className="text-green-400 font-mono font-semibold">
                                ${item.subtotal}
                            </div>
                            {onRemoveItem && (
                                <button
                                    onClick={() => onRemoveItem(item.nombre_producto)}
                                    className="p-1 hover:bg-red-500/20 rounded text-gray-600 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                                    title="Quitar"
                                >
                                    ✕
                                </button>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            <div className="p-4 bg-gray-950/50 border-t border-white/10">
                <div className="flex justify-between items-center mb-4">
                    <span className="text-gray-400 uppercase text-sm tracking-wider">Total</span>
                    <span className="text-3xl font-bold text-white">${total}</span>
                </div>
                <div className="text-center text-xs text-gray-500 italic">
                    Di "Cobrar" para finalizar
                </div>
            </div>
        </div>
    );
};
