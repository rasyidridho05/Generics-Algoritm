import random
import math

# 1. Parameter Generic Algorithm & Define Problem
POPULATION_SIZE = 50       # Ukuran populasi
CHROMOSOME_LENGTH = 32     # 16 bit untuk x1, 16 bit untuk x2
P_CROSSOVER = 0.8          # Probabilitas crossover (Pc)
P_MUTATION = 0.05          # Probabilitas mutasi (Pm)
MAX_GENERATION = 100       # Kriteria penghentian (maksimal iterasi)
X_MIN, X_MAX = -10, 10     # Batas domain x1 dan x2

def calculate_objective(x1, x2):
    """
    Fungsi objektif yang ingin dicari nilai minimumnya.
    f(x1, x2) = -(sin(x1)cos(x2)tan(x1+x2) + 0.5*exp(1 - sqrt(abs(x2))^2))
    Catatan: abs(x2) digunakan untuk menghindari ValueError dari akar kuadrat bernilai negatif.
    """
    try:
        term = (math.sin(x1) * math.cos(x2) * math.tan(x1 + x2)) + (0.5 * math.exp(1 - math.sqrt(abs(x2))**2))  
        
        # Menghindari error akar negatif dengan abs()
        return -(term)
    except OverflowError:
        # Menangani nilai ekstrem dari tan()
        return float('inf')

# 2. Init Population
def create_chromosome(length):
    """Menghasilkan satu kromosom biner acak."""
    return [random.randint(0, 1) for _ in range(length)]

def init_population(pop_size, chrom_len):
    """Menghasilkan populasi awal."""
    return [create_chromosome(chrom_len) for _ in range(pop_size)]

# 3. Decode Chromosome
def decode_chromosome(chromosome):
    """
    Membagi kromosom menjadi dua bagian (untuk x1 dan x2) 
    dan mendekodenya menjadi nilai real di antara batas [-10, 10].
    """
    half = len(chromosome) // 2
    x1_bin = chromosome[:half]
    x2_bin = chromosome[half:]
    
    def binary_to_real(bin_array, r_min, r_max):
        # Konversi array biner ke integer
        integer_val = sum(val * (2 ** idx) for idx, val in enumerate(reversed(bin_array)))
        max_int = (2 ** len(bin_array)) - 1
        # Rumus dekode biner ke real
        return r_min + ((r_max - r_min) / max_int) * integer_val
        
    x1 = binary_to_real(x1_bin, X_MIN, X_MAX)
    x2 = binary_to_real(x2_bin, X_MIN, X_MAX)
    return x1, x2

# 4. Calculate Fitness
def calculate_fitness(chromosome):
    """
    Menghitung fitness. Karena kita mencari nilai minimum dari fungsi objektif,
    semakin kecil nilai fungsi, fitness harus semakin besar.
    Kita menggunakan invers fungsi untuk fitness (atau sekadar menggunakan nilai objektif 
    secara langsung jika menggunakan tournament selection yang mencari nilai terendah).
    Di sini fitness dirancang agar nilai objektif yang lebih kecil memberikan fitness lebih besar.
    """
    x1, x2 = decode_chromosome(chromosome)
    obj_val = calculate_objective(x1, x2)

    return -obj_val 

# 5. Pemilihan Parent 
def tournament_selection(population, k=3):
    """Memilih orangtua menggunakan metode Tournament Selection."""
    best = None
    for _ in range(k):
        ind = random.choice(population)
        if best is None or calculate_fitness(ind) > calculate_fitness(best):
            best = ind
    return best

# 6. Crossover
def single_point_crossover(parent1, parent2, pc):
    """Melakukan crossover satu titik."""
    if random.random() < pc:
        point = random.randint(1, len(parent1) - 1)
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        return child1, child2
    return parent1[:], parent2[:]

# 7. Mutasi
def bit_flip_mutation(chromosome, pm):
    """Melakukan mutasi pembalikan bit."""
    mutated = []
    for bit in chromosome:
        if random.random() < pm:
            mutated.append(1 if bit == 0 else 0)
        else:
            mutated.append(bit)
    return mutated

# Main Program (Switch Generation)
def run_genetic_algorithm():
    print("Inisialisasi Populasi...")
    population = init_population(POPULATION_SIZE, CHROMOSOME_LENGTH)
    
    best_chromosome = None
    best_fitness = float('-inf')
    
    for generation in range(MAX_GENERATION):
        new_population = []
        
        # Elitism: Mempertahankan 2 individu terbaik agar tidak hilang
        population.sort(key=lambda x: calculate_fitness(x), reverse=True)
        new_population.extend(population[:2])
        
        # Membentuk sisa populasi generasi baru
        while len(new_population) < POPULATION_SIZE:
            # 1. Pemilihan orangtua
            p1 = tournament_selection(population)
            p2 = tournament_selection(population)
            
            # 2. Crossover
            c1, c2 = single_point_crossover(p1, p2, P_CROSSOVER)
            
            # 3. Mutasi
            c1 = bit_flip_mutation(c1, P_MUTATION)
            c2 = bit_flip_mutation(c2, P_MUTATION)
            
            new_population.extend([c1, c2])
            
        # Potong jika populasi melebihi ukuran (karena nambah 2 per loop)
        population = new_population[:POPULATION_SIZE]
        
        # Update kromosom terbaik dari generasi ini 
        current_best = max(population, key=lambda x: calculate_fitness(x))
        if calculate_fitness(current_best) > best_fitness:
            best_fitness = calculate_fitness(current_best)
            best_chromosome = current_best
            
        if (generation + 1) % 10 == 0:
            x1, x2 = decode_chromosome(best_chromosome)
            obj_val = calculate_objective(x1, x2)
            print(f"Generasi {generation + 1}: f({x1:.4f}, {x2:.4f}) = {obj_val:.6f}")

    # Output Akhir
    x1, x2 = decode_chromosome(best_chromosome)
    min_val = calculate_objective(x1, x2)
    
    print("\n" + "="*40)
    print("HASIL AKHIR ALGORITMA GENETIKA")
    print("="*40)
    print(f"Kromosom Terbaik : {best_chromosome}")
    print(f"Nilai x1         : {x1}")
    print(f"Nilai x2         : {x2}")
    print(f"Nilai f(x1, x2)  : {min_val}")

if __name__ == "__main__":
    run_genetic_algorithm()