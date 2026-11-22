"use client";

import { useEffect, useState } from "react";
import { inventoryService, Asset } from "@/lib/inventory";
import { ArrowDownToLine, ArrowLeft, CheckCircle2, AlertCircle } from "lucide-react";
import Link from "next/link";
import styles from "../orders.module.css";
import { telemetry } from "../../../../services/telemetry";

export default function InboundPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);

  // Estado del formulario
  const [selectedAssetId, setSelectedAssetId] = useState("");
  const [showPicker, setShowPicker] = useState(false);
  const [quantity, setQuantity] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const data = await inventoryService.getProducts();
        setAssets(data);
        const params = new URLSearchParams(window.location.search);
        const preselectedId = params.get("asset_id")?.trim();
        if (preselectedId && data.some((a) => a.id.toString() === preselectedId)) {
          setSelectedAssetId(preselectedId);
        } else {
          setShowPicker(true);
        }
      } catch (err: any) {
        setErrorMsg(err.message || "No se pudieron cargar los activos.");
      } finally {
        setLoading(false);
      }
    };
    fetchAssets();
  }, []);

  const selectedAsset = assets.find((a) => a.id.toString() === selectedAssetId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");

    if (!selectedAssetId || !quantity || Number(quantity) <= 0) {
      setErrorMsg("Por favor selecciona un activo y una cantidad válida mayor a 0.");
      return;
    }

    setIsSubmitting(true);
    try {
      await inventoryService.createInboundOrder(Number(selectedAssetId), Number(quantity));
      const assetName = assets.find(a => a.id.toString() === selectedAssetId)?.name;
      const assetSku = assets.find(a => a.id.toString() === selectedAssetId)?.sku;
      telemetry.track("inbound_order_created", {
        order_id: crypto.randomUUID(), // Generamos un ID provisorio
        supplier_id_hash: "internal_supply", // Placeholder por ahora
        sku_list_count: 1,
        total_units: Number(quantity),
        expected_delivery_date: new Date().toISOString()
      });

      const addedUnits = Number(quantity);
      setSuccessMsg(`¡Éxito! Se registraron ${quantity} unidades de ${assetName}.`);
      setAssets((prev) =>
        prev.map((a) =>
          a.id.toString() === selectedAssetId
            ? { ...a, current_stock: a.current_stock + addedUnits }
            : a
        )
      );

      // Limpiar solo la cantidad para mantener el activo seleccionado
      setQuantity("");
    } catch (err: any) {
      setErrorMsg(err.message || "Hubo un error al registrar la entrada.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) return <div className={styles.loading}>Cargando formulario...</div>;

  return (
    <div style={{ padding: "2rem" }}>
      <Link href="/inventory/products" className={styles.backLink}>
        <ArrowLeft size={16} /> Volver a Productos
      </Link>

      <div className={styles.container}>
        <header className={styles.header}>
          <h1 className={styles.title}>Registrar Entrada de Activos</h1>
          <p className={styles.subtitle}>Añade nuevo stock al inventario corporativo</p>
        </header>

        {successMsg && (
          <div className={styles.successMessage}>
            <CheckCircle2 size={20} />
            {successMsg}
          </div>
        )}

        {errorMsg && (
          <div className={styles.errorMessage}>
            <AlertCircle size={20} />
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem" }}>
              <label className={styles.label}>Activo a ingresar</label>
              {selectedAsset && !showPicker && (
                <button
                  type="button"
                  onClick={() => setShowPicker(true)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "#34d399",
                    fontSize: "0.78rem",
                    fontWeight: 600,
                    cursor: "pointer",
                    textDecoration: "underline",
                  }}
                >
                  Cambiar activo
                </button>
              )}
            </div>

            {selectedAsset && !showPicker ? (
              <div
                style={{
                  padding: "0.9rem 1rem",
                  borderRadius: "0.65rem",
                  background: "rgba(16, 185, 129, 0.1)",
                  border: "1px solid rgba(16, 185, 129, 0.35)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.35rem",
                }}
              >
                <div style={{ fontWeight: 700, color: "#ffffff", fontSize: "0.95rem" }}>
                  {selectedAsset.name}
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", fontSize: "0.8rem", color: "#a7f3d0" }}>
                  <span>SKU: <strong>{selectedAsset.sku}</strong></span>
                  <span>Depto: <strong>{selectedAsset.department}</strong></span>
                  <span>Stock actual: <strong>{selectedAsset.current_stock} uds.</strong></span>
                </div>
              </div>
            ) : (
              <select
                className={styles.select}
                value={selectedAssetId}
                onChange={(e) => {
                  setSelectedAssetId(e.target.value);
                  if (e.target.value) setShowPicker(false);
                }}
                disabled={isSubmitting}
              >
                <option value="">-- Selecciona un activo --</option>
                {assets.map((asset) => (
                  <option key={asset.id} value={asset.id}>
                    {asset.name} (SKU: {asset.sku})
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>Cantidad recibida</label>
            <input
              type="number"
              className={styles.input}
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              min="1"
              placeholder="Ej: 10"
              disabled={isSubmitting}
            />
          </div>

          <button
            type="submit"
            className={`${styles.btnSubmit} ${styles.btnInbound}`}
            disabled={isSubmitting || !selectedAssetId || !quantity}
          >
            <ArrowDownToLine size={20} />
            {isSubmitting ? "Registrando..." : "Confirmar Entrada"}
          </button>
        </form>
      </div>
    </div>
  );
}
