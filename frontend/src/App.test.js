import { render, screen } from '@testing-library/react';
import App from './App';

test('renders loading state', () => {
  render(<App />);
  const linkElement = screen.getByText(/Загрузка/i);
  expect(linkElement).toBeInTheDocument();
}); 
