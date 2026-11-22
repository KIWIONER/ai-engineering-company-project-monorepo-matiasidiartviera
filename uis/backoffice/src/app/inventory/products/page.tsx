"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { inventoryService, Asset } from "@/lib/inventory";
import {
  Package,
  ArrowDownToLine,
  ArrowUpFromLine,
  AlertCircle,
  CheckCircle2,
  XCircle,
  BarChart3,
  FileText,
  Search,
} from "lucide-react";
import Link from "next/link";
import styles from "./products.module.css";

const PAGE_SIZE = 20;

export default function ProductsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("ALL");
  const [stockFilter, setStockFilter] = useState("ALL");
  const [currentPage, setCurrentPage] = useState(1);
  const listTopRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const data = await inventoryService.getProducts();
        setAssets(data);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Error al cargar los activos";
        setError(msg);
      } finally {
        setLoading(false);
      }
    };
    fetchAssets();
  }, []);

  const departments = useMemo(() => {
    const unique = Array.from(new Set(assets.map((a) => a.department).filter(Boolean)));
    return unique.sort();
  }, [assets]);

  const filteredAssets = useMemo(() => {
    const q = search.trim().toLowerCase();
    return assets.filter((asset) => {
      if (departmentFilter !== "ALL" && asset.department !== departmentFilter) {
        return false;
      }
      if (stockFilter === "HEALTHY" && asset.current_stock <= 5) return false;
      if (stockFilter === "LOW" && (asset.current_stock <= 0 || asset.current_stock > 5)) return false;
      if (stockFilter === "OUT" && asset.current_stock !== 0) return false;
      if (q) {
        const matchesName = asset.name.toLowerCase().includes(q);
        const matchesSku = asset.sku.toLowerCase().includes(q);
        const matchesDept = asset.department.toLowerCase().includes(q);
        if (!matchesName && !matchesSku && !matchesDept) return false;
      }
      return true;
    });
  }, [assets, search, departmentFilter, stockFilter]);

  useEffect(() => {
    setCurrentPage(1);
  }, [search, departmentFilter, stockFilter]);

  const getStockStatus = (stock: number) => {
    if (stock > 5) return { label: "Saludable", className: styles.statusHealthy, Icon: CheckCircle2 };
    if (stock > 0) return { label: "Bajo", className: styles.statusWarning, Icon: AlertCircle };
    return { label: "Agotado", className: styles.statusDanger, Icon: XCircle };
  };

  const healthyCount = assets.filter((a) => a.current_stock > 5).length;
  const alertCount = assets.filter((a) => a.current_stock <= 5).length;

  const totalItems = filteredAssets.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / PAGE_SIZE));
  const safePage = Math.min(currentPage, totalPages);
  const startIdx = (safePage - 1) * PAGE_SIZE;
  const paginatedAssets = filteredAssets.slice(startIdx, startIdx + PAGE_SIZE);
  const rangeStart = totalItems === 0 ? 0 : startIdx + 1;
  const rangeEnd = Math.min(startIdx + PAGE_SIZE, totalItems);

  const goToPage = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
    listTopRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  if (loading) return <div className={styles.loading}>Cargando inventario...</div>;
  if (error) return <div className={styles.error}>{error}</div>;

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <div className={styles.titleWrapper}>
            <Package className={styles.titleIcon} size={30} />
            <h1 className={styles.title}>Activos Corporativos</h1>
          </div>
          <p className={styles.subtitle}>
            Gestión de stock de licencias y equipamiento (Nexova Solutions)
          </p>
        </div>

        <div className={styles.headerLinks}>
          <Link href="/rfps" className={styles.navPillPrimary}>
            <FileText size={16} /> Portal RFPs
          </Link>
          <Link href="/reporting" className={styles.navPillSecondary}>
            <BarChart3 size={16} /> Panel de KPIs
          </Link>
        </div>
      </header>

      {/* KPIs rápidos */}
      <section className={styles.kpiGrid} aria-label="Resumen de inventario">
        <div className={styles.kpiCard}>
          <span className={styles.kpiLabel}>Total Activos</span>
          <strong className={styles.kpiValue}>{assets.length}</strong>
        </div>
        <div className={styles.kpiCard}>
          <span className={styles.kpiLabel}>Stock Saludable</span>
          <strong className={styles.kpiValue} style={{ color: "#6ee7b7" }}>
            {healthyCount}
          </strong>
        </div>
        <div className={styles.kpiCard}>
          <span className={styles.kpiLabel}>Stock Bajo / Agotado</span>
          <strong
            className={styles.kpiValue}
            style={{ color: alertCount > 0 ? "#fde68a" : "#6ee7b7" }}
          >
            {alertCount}
          </strong>
        </div>
      </section>

      {/* Filtros y búsqueda */}
      <div ref={listTopRef} className={styles.filterBar}>
        <div className={styles.searchInputWrap}>
          <Search size={15} className={styles.searchIcon} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por activo, SKU o departamento..."
            className={styles.searchInput}
          />
        </div>

        <select
          aria-label="Filtrar por departamento"
          value={departmentFilter}
          onChange={(e) => setDepartmentFilter(e.target.value)}
          className={styles.filterSelect}
        >
          <option value="ALL">Todos los departamentos</option>
          {departments.map((dept) => (
            <option key={dept} value={dept}>
              {dept}
            </option>
          ))}
        </select>

        <select
          aria-label="Filtrar por nivel de stock"
          value={stockFilter}
          onChange={(e) => setStockFilter(e.target.value)}
          className={styles.filterSelect}
        >
          <option value="ALL">Todos los estados</option>
          <option value="HEALTHY">Stock Saludable (&gt; 5)</option>
          <option value="LOW">Stock Bajo (1–5)</option>
          <option value="OUT">Agotado (0)</option>
        </select>
      </div>

      <div className={styles.listMeta}>
        Mostrando {rangeStart}–{rangeEnd} de {totalItems} activos · Página {safePage} de {totalPages}
      </div>

      <div className={styles.tableContainer}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th scope="col">Activo</th>
              <th scope="col">SKU</th>
              <th scope="col">Departamento</th>
              <th scope="col">Stock Actual</th>
              <th scope="col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {paginatedAssets.length === 0 ? (
              <tr>
                <td colSpan={5} className={styles.emptyState}>
                  No hay activos que coincidan con los filtros seleccionados.
                </td>
              </tr>
            ) : (
              paginatedAssets.map((asset) => {
                const status = getStockStatus(asset.current_stock);
                const StatusIcon = status.Icon;

                return (
                  <tr key={asset.id} className={styles.row}>
                    <td className={styles.assetName}>{asset.name}</td>
                    <td className={styles.sku}>{asset.sku}</td>
                    <td>
                      <span className={styles.deptBadge}>{asset.department}</span>
                    </td>
                    <td>
                      <div className={`${styles.stockBadge} ${status.className}`}>
                        <StatusIcon size={15} />
                        <span>
                          {asset.current_stock} · {status.label}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div className={styles.actions}>
                        <Link
                          href={`/inventory/orders/inbound?asset_id=${encodeURIComponent(String(asset.id))}`}
                          className={`${styles.actionBtn} ${styles.btnInbound}`}
                        >
                          <ArrowDownToLine size={15} />
                          Entrada
                        </Link>
                        <Link
                          href={`/inventory/orders/outbound?asset_id=${encodeURIComponent(String(asset.id))}`}
                          className={`${styles.actionBtn} ${styles.btnOutbound}`}
                        >
                          <ArrowUpFromLine size={15} />
                          Salida
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <nav aria-label="Paginación de activos" className={styles.pagination}>
          <button
            type="button"
            onClick={() => goToPage(safePage - 1)}
            disabled={safePage === 1}
            className={styles.pageBtn}
          >
            &larr; Anterior
          </button>

          {Array.from({ length: totalPages }, (_, idx) => idx + 1).map((pageNum) => {
            const isCurrent = pageNum === safePage;
            return (
              <button
                key={pageNum}
                type="button"
                onClick={() => goToPage(pageNum)}
                aria-current={isCurrent ? "page" : undefined}
                className={`${styles.pageBtn} ${isCurrent ? styles.pageBtnActive : ""}`}
              >
                {pageNum}
              </button>
            );
          })}

          <button
            type="button"
            onClick={() => goToPage(safePage + 1)}
            disabled={safePage === totalPages}
            className={styles.pageBtn}
          >
            Siguiente &rarr;
          </button>
        </nav>
      )}
    </div>
  );
}
