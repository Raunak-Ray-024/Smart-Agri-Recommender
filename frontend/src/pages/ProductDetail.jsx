import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getProduct } from "../api.js";
import StatusMessage from "../components/StatusMessage.jsx";

function TagList({ items }) {
  return (
    <ul className="tags">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

export default function ProductDetail() {
  const { productId } = useParams();
  const [product, setProduct] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    setProduct(null);

    getProduct(productId)
      .then((data) => {
        if (!cancelled) setProduct(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [productId]);

  return (
    <section className="page">
      <Link to="/recommend">&larr; Back to recommendations</Link>

      {loading && <StatusMessage type="loading" text="Loading product details..." />}
      {error && <StatusMessage type="error" title="Could not load this product" text={error} />}

      {product && (
        <article className="detail">
          <span className="badge">{product.category}</span>
          <h1>{product.product_name}</h1>
          <p>{product.description}</p>

          <h2>Intended use</h2>
          <p>
            Used for: <strong>{product.target_problems.join(", ")}</strong>.
          </p>

          <h2>Suitable crops</h2>
          <TagList items={product.suitable_crops} />

          <h2>Suitable growth stages</h2>
          <TagList items={product.suitable_stages} />

          <h2>Target problems</h2>
          <TagList items={product.target_problems} />

          <h2>Manufacturer</h2>
          <p>{product.manufacturer}</p>

          <h2>Source</h2>
          <p>{product.source}</p>

          <p className="note">
            Follow the product label and local agricultural officer advice. This page gives no
            dosage or application instructions.
          </p>
        </article>
      )}
    </section>
  );
}