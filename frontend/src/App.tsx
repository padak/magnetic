import { ChakraProvider, CSSReset } from '@chakra-ui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import Layout from './components/Layout';
import TripList from './pages/TripList';
import TripDetails from './pages/TripDetails';
import CreateTrip from './pages/CreateTrip';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Define routes with the new API
const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <TripList />,
      },
      {
        path: 'trips/new',
        element: <CreateTrip />,
      },
      {
        path: 'trips/:id',
        element: <TripDetails />,
      },
    ],
  },
], {
  future: {
    v7_relativeSplatPath: true
  }
});

function App() {
  return (
    <ChakraProvider>
      <CSSReset />
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </ChakraProvider>
  );
}

export default App;
