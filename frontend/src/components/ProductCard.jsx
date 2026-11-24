import { Link } from "react-router-dom";

export default function ProductCard({ product, rank }) {
  return (
    <article className="card">
      <div className="card-top">
        <span className="rank">#{rank}</span>
        <span className="badge">{product.category}</span>
      </div>
      <h3>{product.product_name}</h3>
      <p className="score">
        Relevance score: <strong>{product.relevance_score}%</strong>
      </p>
      <p>{product.description}</p>
      <p className="reason">
        <strong>Why this product: </strong>
        {product.reason}
      </p>
      <Link className="button" to={`/products/${product.product_id}`}>
        View details
      </Link>
    </article>
  );
}