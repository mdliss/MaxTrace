import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Upload from './pages/Upload';
import Processing from './pages/Processing';
import Results from './pages/Results';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Upload />} />
        <Route path="/processing/:blueprintId" element={<Processing />} />
        <Route path="/results/:blueprintId" element={<Results />} />
      </Routes>
    </Router>
  );
}

export default App;
