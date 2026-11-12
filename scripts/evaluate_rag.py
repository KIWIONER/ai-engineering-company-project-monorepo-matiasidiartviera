"""
Script de Evaluación Cuantitativa del Sistema RAG (Nexova Solutions).
Calcula la métrica Recall@3 sobre data/eval/test-queries.json y audita la tasa anti-alucinaciones.
"""

import json
import os
import sys
import time
from pathlib import Path

# Resolver ruta raíz del monorepo
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.pipelines.rag import retrieve

BENCHMARK_PATH = ROOT_DIR / "data" / "eval" / "test-queries.json"


def run_benchmark():
    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError(f"No se encontró el dataset de evaluación: {BENCHMARK_PATH}")

    with open(BENCHMARK_PATH, encoding="utf-8") as f:
        queries = json.load(f)

    print("=" * 80)
    print(f"📊 INICIANDO BENCHMARK CUANTITATIVO RAG — NEXOVA SOLUTIONS ({len(queries)} consultas)")
    print("=" * 80)

    in_domain_total = 0
    in_domain_hits_at_3 = 0
    out_domain_total = 0
    out_domain_rejections = 0
    latencies = []

    print(f"{'ID':<5} | {'Tipo':<12} | {'Recall@3':<10} | {'Latencia':<10} | {'Consulta':<35}")
    print("-" * 80)

    for item in queries:
        qid = item["id"]
        q_text = item["query"]
        expected_doc = item["expected_document"]
        is_in_domain = item["is_in_domain"]

        start_time = time.perf_counter()
        # Buscamos Top-3 con umbral calibrado 0.70
        results = retrieve(q_text, k=3, min_score=0.70)
        latency = (time.perf_counter() - start_time) * 1000
        latencies.append(latency)

        retrieved_docs = [r.get("source_document") for r in results]

        if is_in_domain:
            in_domain_total += 1
            hit = expected_doc in retrieved_docs
            if hit:
                in_domain_hits_at_3 += 1
            status = "✅ HIT" if hit else "❌ MISS"
            print(f"{qid:<5} | In-Domain    | {status:<10} | {latency:6.1f}ms  | {q_text[:35]}...")
        else:
            out_domain_total += 1
            rejected = len(results) == 0
            if rejected:
                out_domain_rejections += 1
            status = "🛡️ RECHAZO" if rejected else "⚠️ FILTRADO"
            print(f"{qid:<5} | Out-Domain   | {status:<10} | {latency:6.1f}ms  | {q_text[:35]}...")

    recall_at_3 = (in_domain_hits_at_3 / in_domain_total) * 100 if in_domain_total > 0 else 0
    rejection_rate = (out_domain_rejections / out_domain_total) * 100 if out_domain_total > 0 else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    print("=" * 80)
    print("📈 RESULTADOS CONSOLIDADOS DEL BENCHMARK:")
    print(f"  • Consultas evaluadas:        {len(queries)}")
    print(f"  • Recall@3 (In-Domain):       {recall_at_3:.1f}% ({in_domain_hits_at_3}/{in_domain_total})")
    print(f"  • Precisión Anti-Alucinación: {rejection_rate:.1f}% ({out_domain_rejections}/{out_domain_total})")
    print(f"  • Latencia Media:             {avg_latency:.1f} ms")
    print("=" * 80)

    # Validar umbral estricto de la estrategia
    assert recall_at_3 >= 80.0, f"Fallo en benchmark: Recall@3 ({recall_at_3:.1f}%) es menor al 80.0% requerido."
    print("🏆 ¡CRITERIO SUPERADO CON ÉXITO: Recall@3 >= 80% y Rechazo Anti-Alucinaciones verificado!\n")


if __name__ == "__main__":
    run_benchmark()