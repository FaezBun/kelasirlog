import os
import re
import time
import random
import threading
import multiprocessing
import matplotlib.pyplot as plt
from tqdm import tqdm
from collections import Counter

# --- CONFIGURATION ---
LOG_FILE = "15milserver_forensic.log"
TOTAL_LINES = 15_000_000  # 1 Juta baris
NUM_CORES = multiprocessing.cpu_count()

# --- 1. DATA GENERATOR (RANDOMIZED ATTACKS) ---
def generate_data():
    if os.path.exists(LOG_FILE):
        print(f"[*] Log file '{LOG_FILE}' exists. Skipping generation.")
        return
    
    threat_types = [
        "SQL_INJECTION_DETECTED",
        "BRUTE_FORCE_ATTEMPT",
        "XSS_ATTACK_DETECTED",
        "PATH_TRAVERSAL_ATTACK",
        "UNAUTHORIZED_ADMIN_ACCESS"
    ]
    
    # Kebarangkalian 8% untuk ancaman (80,000 / 1,000,000)
    PROBABILITY = 0.08 
    
    print(f"[*] Generating {TOTAL_LINES:,} lines of randomized forensic logs...")
    with open(LOG_FILE, 'w') as f:
        for i in range(TOTAL_LINES):
            if random.random() < PROBABILITY:
                threat = random.choice(threat_types)
                ip = f"10.0.0.{random.randint(1, 254)}"
                f.write(f"{ip} - [CRITICAL] {threat} - /target/path_{i}\n")
            else:
                ip = f"192.168.1.{random.randint(1, 254)}"
                f.write(f"{ip} - [INFO] User access - /home\n")
    print("[+] Data Generation Complete.\n")

# --- 2. CONCURRENT TECHNIQUE (THREADING) ---
def read_logs_concurrently(filename):
    print(f"[*] [CONCURRENCY] Starting Threaded I/O to read {filename}...")
    logs = []
    
    def thread_worker():
        with open(filename, 'r') as f:
            logs.extend(f.readlines())
            
    thread = threading.Thread(target=thread_worker)
    start_io = time.perf_counter()
    thread.start()
    thread.join()
    print(f"[+] Threaded I/O completed in {time.perf_counter() - start_io:.4f}s")
    return logs

# --- 3. WORKER LOGIC (EXTRACT ATTACK NAMES & INFO) ---
def find_patterns(lines):
    # Kita cari [CRITICAL] untuk attack DAN [INFO] untuk normal login
    threat_pattern = re.compile(r"\[CRITICAL\] (\w+)")
    info_pattern = re.compile(r"\[INFO\]")
    
    results = {
        'threats': [],
        'info_count': 0
    }
    
    for line in lines:
        match = threat_pattern.search(line)
        if match:
            results['threats'].append(match.group(1))
        elif info_pattern.search(line):
            results['info_count'] += 1
            
    return results

# --- 4. PARALLEL TECHNIQUE (MULTIPROCESSING) ---
def run_parallel(data):
    print(f"[*] [PARALLELISM] Distributing workload to {NUM_CORES} CPU cores...")
    chunk_size = len(data) // NUM_CORES
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    
    start_time = time.perf_counter()
    with multiprocessing.Pool(processes=NUM_CORES) as pool:
        results = list(tqdm(pool.imap_unordered(find_patterns, chunks), 
                            total=len(chunks), 
                            desc="Parallel Processing"))
    
    duration = time.perf_counter() - start_time
    
    # Gabungkan hasil dari semua core
    all_threats = []
    total_info = 0
    for res in results:
        all_threats.extend(res['threats'])
        total_info += res['info_count']
        
    attack_stats = Counter(all_threats)
    
    return attack_stats, total_info, duration

# --- 5. SEQUENTIAL (FOR BENCHMARKING) ---
def run_sequential(data):
    print(f"[*] [SEQUENTIAL] Running single-core processing benchmark...")
    sample_size = len(data) // 5 
    start_time = time.perf_counter()
    
    for line in tqdm(data[:sample_size], desc="Sequential Processing"):
        find_patterns([line])
        
    duration = (time.perf_counter() - start_time) * 5
    return duration

# --- 6. PERFORMANCE GRAPH GENERATOR ---
def save_performance_graph(seq_time, par_time):
    methods = ['Sequential (1 Core)', f'Parallel ({NUM_CORES} Cores)']
    times = [seq_time, par_time]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(methods, times, color=['#ff7675', '#55efc4'])
    
    plt.ylabel('Execution Time (Seconds)')
    plt.title(f'ITT440 Performance Benchmark: Log Forensics\nData Size: {TOTAL_LINES:,} Lines')
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.02, f'{yval:.2f}s', ha='center', va='bottom', fontweight='bold')

    plt.savefig('performance_result.png')
    print("\n[+] SUCCESS: Performance graph saved as 'performance_result.png'")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    generate_data()
    all_logs = read_logs_concurrently(LOG_FILE)
    
    # 1. Benchmark Sequential
    seq_duration = run_sequential(all_logs)
    
    # 2. Benchmark Parallel & Detailed Analysis
    attack_stats, total_info, par_duration = run_parallel(all_logs)
    total_threats = sum(attack_stats.values())
    
    # 3. Print Detailed Report
    print("\n" + "="*55)
    print(f"{'DETAILED FORENSIC ANALYSIS REPORT':^55}")
    print("-" * 55)
    for attack, count in attack_stats.items():
        print(f"{attack:<35}: {count:,} cases")
    print("-" * 55)
    print(f"TOTAL THREATS DETECTED             : {total_threats:,}")
    print(f"TOTAL NORMAL LOGINS (INFO)         : {total_info:,}")
    print(f"TOTAL LINES PROCESSED              : {len(all_logs):,}")
    print("="*55)
    
    # 4. Print Performance Summary
    speedup = seq_duration / par_duration
    print("\n" + "="*55)
    print(f"{'PERFORMANCE COMPARISON (T490s)':^55}")
    print("-" * 55)
    print(f"Sequential Time : {seq_duration:.2f}s")
    print(f"Parallel Time   : {par_duration:.2f}s")
    print(f"Speedup Factor  : {speedup:.2f}x Faster")
    print("="*55)
    
    save_performance_graph(seq_duration, par_duration)
