import EngineShowcase from "@/components/EngineShowcase";
import {
  Nav, Hero, Stats, Modalities, HowItWorks, CommandTable,
  Architecture, Safety, Evaluation, GetStarted, FAQ, Footer,
} from "@/components/Sections";

export default function Home() {
  return (
    <>
      <Nav />
      <main id="main">
        <Hero />
        <Stats />
        <Modalities />
        <EngineShowcase />
        <HowItWorks />
        <CommandTable />
        <Architecture />
        <Safety />
        <Evaluation />
        <GetStarted />
        <FAQ />
      </main>
      <Footer />
    </>
  );
}
