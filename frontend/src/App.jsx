import { Link, NavLink, Route, Routes } from "react-router-dom";
import Home from "./pages/Home.jsx";
import Recommend from "./pages/Recommend.jsx";
import ProductDetail from "./pages/ProductDetail.jsx";

function NotFound() {
  return (
    <section className="page">
      <h1>Page not found</h1>
      <p>The page you are looking for does not exist.</p>
      <Link className="button" to="/">Go to Home</Link>
    </section>
  );
}

export default function App() {
  return (
    <div className="app">
      <header className="site-header">
        <Link className="brand" to="/">AgriSmart</Link>
        <nav className="nav" aria-label="Main navigation">
          <NavLink to="/" end>Home</NavLink>
          <NavLink to="/recommend">Get Recommendations</NavLink>
        </nav>
      </header>

      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/recommend" element={<Recommend />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>

      <footer className="site-footer">
        Products shown are illustrative sample entries and are not verified recommendations.
        Always follow product labels and local agricultural officer advice.
      </footer>
    </div>
  );
}