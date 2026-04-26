import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { ProblemFraming } from './components/ProblemFraming';
import { FeaturedPRsTabs } from './components/FeaturedPRsTabs';
import { LiveMode } from './components/LiveMode';
import { HowItWorks } from './components/HowItWorks';
import { Footer } from './components/Footer';
import { featuredPRs } from './data';

function App() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50/30">
      <Navbar />
      <main className="flex-1">
        <Hero />
        <ProblemFraming />
        <FeaturedPRsTabs prs={featuredPRs} />
        <LiveMode />
        <HowItWorks />
      </main>
      <Footer />
    </div>
  );
}

export default App;
