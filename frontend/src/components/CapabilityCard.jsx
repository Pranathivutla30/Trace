// Starter presentational shell for one TRACE capability.

export default function CapabilityCard({ title, question }) {
  return (
    <section>
      <h2>{title}</h2>
      <p>{question}</p>
    </section>
  );
}
