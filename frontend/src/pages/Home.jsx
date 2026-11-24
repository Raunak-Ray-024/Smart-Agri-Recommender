import { Link } from "react-router-dom";

const STEPS = [
  { title: "1. Choose your crop", text: "Pick the crop you are growing." },
  { title: "2. Select the stage and problem", text: "Tell us the growth stage and the problem you see." },
  { title: "3. Get 3 product ideas", text: "See the best matching products and why each one matches." },
];

export default function Home() {
  return (
    <>
      <section className="hero">
        <h1>Find the right farm products for your crop</h1>
        <p>
          AgriSmart suggests agricultural products based on your crop, its growth stage and the
          problem you are facing. Each suggestion comes with a simple reason.
        </p>
        <Link className="button button-primary" to="/recommend">
          Get Recommendations
        </Link>
      </section>

      <section className="page" aria-labelledby="how-title">
        <h2 id="how-title">How it works</h2>
        <div className="grid">
          {STEPS.map((step) => (
            <div className="card" key={step.title}>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </div>
          ))}
        </div>
        <p className="note">
          This is a learning project. The product data is a small illustrative sample and does not
          replace advice from a local agricultural expert.
        </p>
      </section>
    </>
  );
}