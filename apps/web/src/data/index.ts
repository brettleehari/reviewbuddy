import type { ScoredPR } from '../types';
import prometheus from './prometheus-6643.json';
import react from './react-18580.json';
import rails from './rails-38211.json';
import transformers from './transformers-8308.json';
import transformersBert from './transformers-4874.json';

export const featuredPRs: ScoredPR[] = [
  rails as ScoredPR,
  react as ScoredPR,
  transformers as ScoredPR,
  prometheus as ScoredPR,
  transformersBert as ScoredPR,
];
