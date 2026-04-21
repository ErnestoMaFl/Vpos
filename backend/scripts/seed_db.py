import os
import re
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Load env vars
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

raw_data = """
    # --- BOTANAS Y SNACKS ---
    {"id": 1001, "nombre": "Takis Fuego Bolsa Grande", "precio": 38, "stock": 22},
    {"id": 1002, "nombre": "Papas Sabritas Sal 45g", "precio": 18, "stock": 40},
    {"id": 1003, "nombre": "Doritos Nacho 58g", "precio": 19, "stock": 35},
    {"id": 1004, "nombre": "Cheetos Torciditos 52g", "precio": 15, "stock": 50},
    {"id": 1005, "nombre": "Ruffles Queso 50g", "precio": 19, "stock": 30},
    {"id": 1006, "nombre": "Pinguinos Marinela 2 pzs", "precio": 22, "stock": 15},
    {"id": 1007, "nombre": "Chocorroles Marinela 2 pzs", "precio": 22, "stock": 12},
    {"id": 1008, "nombre": "Barritas Fresa Marinela", "precio": 18, "stock": 20},
    {"id": 1009, "nombre": "Gansito Marinela", "precio": 17, "stock": 25},
    {"id": 1010, "nombre": "Papas Barcel Sal", "precio": 18, "stock": 18},
    {"id": 1011, "nombre": "Hot Nuts Original", "precio": 15, "stock": 45},
    {"id": 1012, "nombre": "Cacahuates Mafer Salados", "precio": 25, "stock": 15},
    {"id": 1013, "nombre": "Bombones Blancos 100g", "precio": 20, "stock": 10},
    {"id": 1014, "nombre": "Palomitas ACT II Mantequilla", "precio": 16, "stock": 30},
    {"id": 1015, "nombre": "Papas Pringles Original", "precio": 55, "stock": 12},

    # --- BEBIDAS Y REFRESCOS ---
    {"id": 2001, "nombre": "Coca Cola 600ml", "precio": 18, "stock": 100},
    {"id": 2002, "nombre": "Coca Cola 2.5L", "precio": 38, "stock": 50},
    {"id": 2003, "nombre": "Pepsi 600ml", "precio": 16, "stock": 80},
    {"id": 2004, "nombre": "Sprite 600ml", "precio": 17, "stock": 40},
    {"id": 2005, "nombre": "Sidral Mundet 600ml", "precio": 17, "stock": 30},
    {"id": 2006, "nombre": "Agua Ciel 1L", "precio": 12, "stock": 60},
    {"id": 2007, "nombre": "Agua Bonafont 1.5L", "precio": 16, "stock": 45},
    {"id": 2008, "nombre": "Jugo Del Valle Naranja 413ml", "precio": 16, "stock": 35},
    {"id": 2009, "nombre": "Jugo Boing Guayaba 250ml", "precio": 11, "stock": 50},
    {"id": 2010, "nombre": "Gatorade Ponche 600ml", "precio": 26, "stock": 25},
    {"id": 2011, "nombre": "Red Bull 250ml", "precio": 52, "stock": 15},
    {"id": 2012, "nombre": "Monster Energy 473ml", "precio": 48, "stock": 18},
    {"id": 2013, "nombre": "Peñafiel Mineral 600ml", "precio": 16, "stock": 30},
    {"id": 2014, "nombre": "Jarritos Tamarindo 600ml", "precio": 14, "stock": 40},
    {"id": 2015, "nombre": "Te Arizona 680ml", "precio": 20, "stock": 25},

    # --- LÁCTEOS Y HUEVOS ---
    {"id": 3001, "nombre": "Leche Alpura Clásica 1L", "precio": 27, "stock": 48},
    {"id": 3002, "nombre": "Leche Lala Deslactosada 1L", "precio": 29, "stock": 40},
    {"id": 3003, "nombre": "Huevo Blanco 12 piezas", "precio": 35, "stock": 20},
    {"id": 3004, "nombre": "Yogur Lala Fresa 220g", "precio": 12, "stock": 30},
    {"id": 3005, "nombre": "Yoplait Griego Natural", "precio": 18, "stock": 15},
    {"id": 3006, "nombre": "Queso Panela Nochebuena 400g", "precio": 75, "stock": 10},
    {"id": 3007, "nombre": "Queso Oaxaca 250g", "precio": 58, "stock": 12},
    {"id": 3008, "nombre": "Mantequilla Primavera 90g", "precio": 16, "stock": 25},
    {"id": 3009, "nombre": "Media Crema Nestle 190g", "precio": 17, "stock": 35},
    {"id": 3010, "nombre": "Leche Condensada La Lechera", "precio": 28, "stock": 20},
    {"id": 3011, "nombre": "Leche Evaporada Carnation", "precio": 22, "stock": 25},
    {"id": 3012, "nombre": "Yakult Individual", "precio": 10, "stock": 40},
    {"id": 3013, "nombre": "Danonino Fresa", "precio": 8, "stock": 50},
    {"id": 3014, "nombre": "Crema Alpura 450ml", "precio": 36, "stock": 15},
    {"id": 3015, "nombre": "Queso Americano 8 rebanadas", "precio": 24, "stock": 20},

    # --- GALLETAS Y PANADERÍA ---
    {"id": 4001, "nombre": "Galletas Marias Gamesa", "precio": 15, "stock": 60},
    {"id": 4002, "nombre": "Galletas Oreo 114g", "precio": 18, "stock": 45},
    {"id": 4003, "nombre": "Galletas Emperador Chocolate", "precio": 19, "stock": 35},
    {"id": 4004, "nombre": "Pan Blanco Bimbo Grande", "precio": 48, "stock": 20},
    {"id": 4005, "nombre": "Pan Integral Bimbo", "precio": 52, "stock": 15},
    {"id": 4006, "nombre": "Donas Bimbo 4 pzs", "precio": 24, "stock": 12},
    {"id": 4007, "nombre": "Pan Tostado Clásico Bimbo", "precio": 38, "stock": 18},
    {"id": 4008, "nombre": "Medias Noches Bimbo 8 pzs", "precio": 42, "stock": 20},
    {"id": 4009, "nombre": "Galletas Saladitas Gamesa", "precio": 18, "stock": 30},
    {"id": 4010, "nombre": "Galletas Ritz 100g", "precio": 17, "stock": 25},
    {"id": 4011, "nombre": "Galletas Animalitos 500g", "precio": 35, "stock": 10},
    {"id": 4012, "nombre": "Mantecadas Bimbo 4 pzs", "precio": 26, "stock": 15},
    {"id": 4013, "nombre": "Principe Marinela Chocolate", "precio": 20, "stock": 22},
    {"id": 4014, "nombre": "Galletas Arcoiris", "precio": 19, "stock": 18},
    {"id": 4015, "nombre": "Tortillinas Tía Rosa 12 pzs", "precio": 28, "stock": 30},

    # --- ABARROTES BÁSICOS ---
    {"id": 5001, "nombre": "Arroz Blanco 1kg", "precio": 26, "stock": 40},
    {"id": 5002, "nombre": "Frijol Negro Verde Valle 1kg", "precio": 38, "stock": 35},
    {"id": 5003, "nombre": "Aceite Nutrioli 850ml", "precio": 42, "stock": 30},
    {"id": 5004, "nombre": "Azúcar Estándar 1kg", "precio": 28, "stock": 50},
    {"id": 5005, "nombre": "Sal de Mesa 1kg", "precio": 14, "stock": 60},
    {"id": 5006, "nombre": "Pasta Spaghetti La Moderna", "precio": 11, "stock": 80},
    {"id": 5007, "nombre": "Pasta Codo No. 2 La Moderna", "precio": 11, "stock": 80},
    {"id": 5008, "nombre": "Harina de Trigo Maseca 1kg", "precio": 22, "stock": 40},
    {"id": 5009, "nombre": "Harina Hot Cakes Pronto", "precio": 28, "stock": 20},
    {"id": 5010, "nombre": "Puré de Tomate Del Fuerte", "precio": 10, "stock": 60},
    {"id": 5011, "nombre": "Lentejas Verde Valle 500g", "precio": 24, "stock": 25},
    {"id": 5012, "nombre": "Atún Herdez en Agua", "precio": 21, "stock": 45},
    {"id": 5013, "nombre": "Atún Dolores en Aceite", "precio": 21, "stock": 45},
    {"id": 5014, "nombre": "Sardina en Tomate Pescador", "precio": 35, "stock": 15},
    {"id": 5015, "nombre": "Mayonesa Hellmanns 190g", "precio": 28, "stock": 20},
    {"id": 5016, "nombre": "Mostaza McCormick 200g", "precio": 18, "stock": 25},
    {"id": 5017, "nombre": "Salsa Valentina Etiqueta Amarilla", "precio": 16, "stock": 50},
    {"id": 5018, "nombre": "Catsup del Monte 320g", "precio": 20, "stock": 30},
    {"id": 5019, "nombre": "Chiles Jalapeños La Costeña 220g", "precio": 15, "stock": 40},
    {"id": 5020, "nombre": "Vinagre Blanco Casero 1L", "precio": 18, "stock": 20},

    # --- DESAYUNO Y CAFÉ ---
    {"id": 6001, "nombre": "Café Nescafe Clásico 120g", "precio": 85, "stock": 15},
    {"id": 6002, "nombre": "Café Soluble Legal 180g", "precio": 65, "stock": 20},
    {"id": 6003, "nombre": "Chocolate Abuelita 6 tablillas", "precio": 82, "stock": 12},
    {"id": 6004, "nombre": "Chocomilk lata 400g", "precio": 55, "stock": 18},
    {"id": 6005, "nombre": "Zucaritas Kellogg's 300g", "precio": 45, "stock": 20},
    {"id": 6006, "nombre": "Choco Krispis 300g", "precio": 45, "stock": 20},
    {"id": 6007, "nombre": "Avena Quaker 400g", "precio": 28, "stock": 30},
    {"id": 6008, "nombre": "Miel Carlota 300g", "precio": 65, "stock": 10},
    {"id": 6009, "nombre": "Mermelada McCormick Fresa", "precio": 38, "stock": 15},
    {"id": 6010, "nombre": "Cereal Corn Flakes Kellogg's", "precio": 42, "stock": 25},
    {"id": 6011, "nombre": "Sustituto de Crema Coffe Mate", "precio": 48, "stock": 18},
    {"id": 6012, "nombre": "Té de Manzanilla McCormick", "precio": 22, "stock": 30},
    {"id": 6013, "nombre": "Grenetina Duche", "precio": 15, "stock": 40},
    {"id": 6014, "nombre": "Polvo para Hornear Royal", "precio": 24, "stock": 15},
    {"id": 6015, "nombre": "Gelatina Jello Fresa", "precio": 14, "stock": 50},

    # --- CUIDADO PERSONAL ---
    {"id": 7001, "nombre": "Jabón Zote Blanco 400g", "precio": 24, "stock": 40},
    {"id": 7002, "nombre": "Jabón Palmolive Naturals", "precio": 18, "stock": 45},
    {"id": 7003, "nombre": "Shampoo Pantene 400ml", "precio": 68, "stock": 20},
    {"id": 7004, "nombre": "Pasta Dental Colgate 100ml", "precio": 35, "stock": 35},
    {"id": 7005, "nombre": "Cepillo Dental Colgate", "precio": 28, "stock": 25},
    {"id": 7006, "nombre": "Desodorante Rexona Hombre", "precio": 55, "stock": 15},
    {"id": 7007, "nombre": "Desodorante Lady Speed Stick", "precio": 52, "stock": 15},
    {"id": 7008, "nombre": "Papel Higiénico Regio 4 rollos", "precio": 32, "stock": 50},
    {"id": 7009, "nombre": "Toallas Femeninas Saba 10 pzs", "precio": 38, "stock": 30},
    {"id": 7010, "nombre": "Rastrillo Gillette Prestobarba", "precio": 22, "stock": 40},
    {"id": 7011, "nombre": "Crema Nivea Tarro 100ml", "precio": 45, "stock": 20},
    {"id": 7012, "nombre": "Talco para Pies Eficaz", "precio": 35, "stock": 15},
    {"id": 7013, "nombre": "Gel para Cabello Ego 200ml", "precio": 24, "stock": 25},
    {"id": 7014, "nombre": "Enjuague Bucal Listerine", "precio": 75, "stock": 10},
    {"id": 7015, "nombre": "Cotonetes Johnson 100 pzs", "precio": 25, "stock": 20},

    # --- LIMPIEZA DEL HOGAR ---
    {"id": 8001, "nombre": "Detergente Ariel 1kg", "precio": 48, "stock": 30},
    {"id": 8002, "nombre": "Detergente Roma 1kg", "precio": 36, "stock": 35},
    {"id": 8003, "nombre": "Cloro Los Patos 1L", "precio": 16, "stock": 50},
    {"id": 8004, "nombre": "Limpiador Fabuloso Lavanda 1L", "precio": 24, "stock": 40},
    {"id": 8005, "nombre": "Lavatrastes Axion Limón 400ml", "precio": 28, "stock": 30},
    {"id": 8006, "nombre": "Suavizante Downy 800ml", "precio": 35, "stock": 25},
    {"id": 8007, "nombre": "Fibras Scotch-Brite 1 pz", "precio": 18, "stock": 40},
    {"id": 8008, "nombre": "Bolsas de Basura Medianas", "precio": 32, "stock": 20},
    {"id": 8009, "nombre": "Insecticida Baygon", "precio": 75, "stock": 12},
    {"id": 8010, "nombre": "Aromatizante Glade Aerosol", "precio": 42, "stock": 15},
    {"id": 8011, "nombre": "Servilletas Pétalo 100 pzs", "precio": 18, "stock": 60},
    {"id": 8012, "nombre": "Pinol 1L", "precio": 22, "stock": 30},
    {"id": 8013, "nombre": "Windex Limpiador Vidrios", "precio": 45, "stock": 10},
    {"id": 8014, "nombre": "Pastilla Sanitaria Pato", "precio": 16, "stock": 25},
    {"id": 8015, "nombre": "Guantes de Limpieza", "precio": 28, "stock": 15},

    # --- VARIEDAD / FERRETERÍA BÁSICA ---
    {"id": 9001, "nombre": "Pilas AA Energizer 2 pzs", "precio": 55, "stock": 20},
    {"id": 9002, "nombre": "Pilas AAA Duracell 2 pzs", "precio": 58, "stock": 18},
    {"id": 9003, "nombre": "Encendedor Bic", "precio": 15, "stock": 40},
    {"id": 9004, "nombre": "Cillos de Madera 50 pzs", "precio": 8, "stock": 100},
    {"id": 9005, "nombre": "Velas de Cera blanca 2 pzs", "precio": 12, "stock": 30},
    {"id": 9006, "nombre": "Foco LED 10W", "precio": 35, "stock": 25},
    {"id": 9007, "nombre": "Cinta Canela 40m", "precio": 28, "stock": 15},
    {"id": 9008, "nombre": "Pegamento Kola Loka", "precio": 25, "stock": 20},
    {"id": 9009, "nombre": "Esponja Multiusos", "precio": 10, "stock": 50},
    {"id": 9010, "nombre": "Papel Aluminio Reynold", "precio": 38, "stock": 15},
    {"id": 9011, "nombre": "Bolsas para Sándwich", "precio": 22, "stock": 30},
    {"id": 9012, "nombre": "Platos Desechables 20 pzs", "precio": 35, "stock": 25},
    {"id": 9013, "nombre": "Vasos Desechables 20 pzs", "precio": 28, "stock": 30},
    {"id": 9014, "nombre": "Tenedores de Plástico", "precio": 18, "stock": 40},
    {"id": 9015, "nombre": "Servitallas Kleenex", "precio": 45, "stock": 20},

    # --- CONDIMENTOS Y VARIOS ---
    {"id": 9101, "nombre": "Caldo de Pollo Knorr 8 cubos", "precio": 15, "stock": 60},
    {"id": 9102, "nombre": "Canela en Rama 50g", "precio": 22, "stock": 15},
    {"id": 9103, "nombre": "Pimienta Negra Molida", "precio": 18, "stock": 20},
    {"id": 9104, "nombre": "Ajo en Polvo", "precio": 18, "stock": 20},
    {"id": 9105, "nombre": "Polvo para Agua Zuko", "precio": 5, "stock": 150},
    {"id": 9106, "nombre": "Polvo para Agua Tang", "precio": 6, "stock": 120},
    {"id": 9107, "nombre": "Vainilla Liquida 250ml", "precio": 25, "stock": 15},
    {"id": 9108, "nombre": "Salsa Inglesa 145ml", "precio": 32, "stock": 12},
    {"id": 9109, "nombre": "Salsa Jugo Maggi 100ml", "precio": 38, "stock": 10},
    {"id": 9110, "nombre": "Tajín Polvo 142g", "precio": 35, "stock": 25},
    {"id": 9111, "nombre": "Colorante Vegetal", "precio": 12, "stock": 20},
    {"id": 9112, "nombre": "Levadura Seca Tradi-Pan", "precio": 10, "stock": 30},
    {"id": 9113, "nombre": "Bicarbonato de Sodio", "precio": 12, "stock": 40},
    {"id": 9114, "nombre": "Aceite de Oliva 250ml", "precio": 85, "stock": 8},
    {"id": 9115, "nombre": "Vinagre de Manzana", "precio": 20, "stock": 15},

    # --- PRODUCTOS DE MASCOTAS ---
    {"id": 9201, "nombre": "Pedigree Adulto 2kg", "precio": 145, "stock": 10},
    {"id": 9202, "nombre": "Whiskas Gato Carne 1.5kg", "precio": 130, "stock": 12},
    {"id": 9203, "nombre": "Sobre Pedigree Res", "precio": 15, "stock": 40},
    {"id": 9204, "nombre": "Sobre Whiskas Atún", "precio": 16, "stock": 35},
    {"id": 9205, "nombre": "Hueso de Carnaza Mediano", "precio": 25, "stock": 20},
"""

def clean_and_parse(data):
    lines = data.strip().split('\n')
    products = []
    current_category = "General"
    
    new_id_counter = 1
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect category
        if line.startswith("# ---") and line.endswith("---"):
            current_category = line.replace("# ---", "").replace("---", "").strip()
            continue
            
        if line.startswith("#"):
            continue

        # Parse JSON-like line
        # Removing trailing comma if present
        if line.endswith(','):
            line = line[:-1]
            
        try:
            item = json.loads(line)
            
            # Metadata Extraction Heuristics
            nombre = item['nombre']
            
            # Unit extraction (e.g., 600ml, 1kg, 2 pzs)
            unit_match = re.search(r'\b(\d+(?:\.\d+)?\s?(?:ml|L|g|kg|pzs|piezas))\b', nombre, re.IGNORECASE)
            unidad = unit_match.group(1) if unit_match else "Unidad"
            
            # Brand extraction (Simplistic: First Word, or specific logic)
            # Common brands in list: Sabritas, Marinela, Coca Cola, Pepsi, etc.
            # We can try to grab the second valid word if the first is generic like 'Papas', 'Galletas'
            generics = ["Papas", "Galletas", "Jugo", "Leche", "Queso", "Pan", "Jabón", "Shampoo", "Pasta", "Desodorante", "Detergente"]
            parts = nombre.split()
            marca = parts[0]
            if len(parts) > 1 and parts[0] in generics:
                marca = parts[1]
                
                marca = "Pepsi"
                
            product = {
                "id": new_id_counter, 
                "nombre": nombre, 
                "precio_venta": item['precio'], 
                "precio_compra": round(item['precio'] * 0.7, 2), # Derived mandatory field
                "stock_actual": item['stock'], 
                "unidad_medida": unidad,
                "descripcion": f"{marca} {nombre} ({current_category})"
            }
            products.append(product)
            new_id_counter += 1
            
        except json.JSONDecodeError:
            print(f"Skipping invalid line: {line}")
            
    return products

def seed_db():
    print("Parsing data...")
    products = clean_and_parse(raw_data)
    print(f"Parsed {len(products)} products.")
    
    # Batch insert
    try:
        # Note: Truncate was done via SQL to handle RESTART IDENTITY properly
        
        # Insert in batches of 50
        batch_size = 50
        for i in range(0, len(products), batch_size):
            batch = products[i:i+batch_size]
            print(f"Inserting batch {i} to {i+batch_size}...")
            supabase.table("vpos_productos").insert(batch).execute()
            
        print("Success! Database populated.")
        
    except Exception as e:
        print(f"Error seeding database: {e}")

if __name__ == "__main__":
    seed_db()
