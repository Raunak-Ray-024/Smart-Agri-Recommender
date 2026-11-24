import { useCallback, useEffect, useState } from "react";
import { getOptions, getRecommendations } from "../api.js";
import SelectField from "../components/SelectField.jsx";
import ProductCard from "../components/ProductCard.jsx";
import StatusMessage from "../components/StatusMessage.jsx";

export default function Recommend() {
  const [options, setOptions] = useState(null);
  const [optionsError, setOptionsError] = useState("");
  const [loadingOptions, setLoadingOptions] = useState(true);

  const [form, setForm] = useState({ crop: "", stage: "", problem: "" });
  const [fieldErrors, setFieldErrors] = useState({});

  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const loadOptions = useCallback(async () => {
    setLoadingOptions(true);
    setOptionsError("");
    try {
      setOptions(await getOptions());
    } catch (error) {
      setOptionsError(error.message);
    } finally {
      setLoadingOptions(false);
    }
  }, []);

  useEffect(() => {
    loadOptions();
  }, [loadOptions]);

  function updateField(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
    setFieldErrors((current) => ({ ...current, [name]: "" }));
  }

  function validate() {
    const errors = {};
    if (!form.crop) errors.crop = "Please select a crop.";
    if (!form.stage) errors.stage = "Please select a growth stage.";
    if (!form.problem) errors.problem = "Please select a problem.";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    setSubmitError("");
    setResult(null);
    try {
      setResult(await getRecommendations(form));
    } catch (error) {
      setSubmitError(error.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="page">
      <h1>Get Recommendations</h1>
      <p>Select your crop, its growth stage and the problem you want to solve.</p>

      {loadingOptions && <StatusMessage type="loading" text="Loading choices..." />}

      {optionsError && (
        <StatusMessage
          type="error"
          title="Could not load the choices"
          text={optionsError}
          actionLabel="Try again"
          onAction={loadOptions}
        />
      )}

      {options && (
        <form className="form" onSubmit={handleSubmit} noValidate>
          <SelectField
            id="crop"
            label="Crop"
            value={form.crop}
            options={options.crops}
            onChange={(value) => updateField("crop", value)}
            error={fieldErrors.crop}
            placeholder="Select a crop"
          />
          <SelectField
            id="stage"
            label="Growth stage"
            value={form.stage}
            options={options.stages}
            onChange={(value) => updateField("stage", value)}
            error={fieldErrors.stage}
            placeholder="Select a growth stage"
          />
          <SelectField
            id="problem"
            label="Problem"
            value={form.problem}
            options={options.problems}
            onChange={(value) => updateField("problem", value)}
            error={fieldErrors.problem}
            placeholder="Select a problem"
          />
          <button type="submit" className="button button-primary" disabled={submitting}>
            {submitting ? "Finding products..." : "Show Recommended Products"}
          </button>
        </form>
      )}

      {submitting && <StatusMessage type="loading" text="Finding the best products..." />}

      {submitError && (
        <StatusMessage type="error" title="Something went wrong" text={submitError} />
      )}

      {result && result.count === 0 && (
        <StatusMessage type="empty" title="No matching products" text={result.message} />
      )}

      {result && result.count > 0 && (
        <div className="results">
          <h2>Recommended products</h2>
          <p>
            For <strong>{result.crop}</strong> at the <strong>{result.stage}</strong> stage with{" "}
            <strong>{result.problem}</strong>. {result.message}
          </p>
          <div className="grid">
            {result.recommendations.map((product, index) => (
              <ProductCard key={product.product_id} product={product} rank={index + 1} />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}