import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Button,
  Flex,
  Grid,
  Heading,
  Text,
  useToast,
  Select,
  Badge,
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { tripService } from '../api/tripService';
import { Trip } from '../types/trip';

const TripList = () => {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string>('');
  const navigate = useNavigate();
  const toast = useToast();

  const { data, isLoading, error } = useQuery({
    queryKey: ['trips', page, status],
    queryFn: () => tripService.listTrips(page, 10, status),
  });

  if (error) {
    toast({
      title: 'Error loading trips',
      description: error instanceof Error ? error.message : 'An error occurred',
      status: 'error',
      duration: 5000,
      isClosable: true,
    });
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'planning':
        return 'blue';
      case 'booked':
        return 'green';
      case 'completed':
        return 'gray';
      default:
        return 'yellow';
    }
  };

  const TripCard = ({ trip }: { trip: Trip }) => (
    <Box
      p={5}
      shadow="md"
      borderWidth="1px"
      borderRadius="lg"
      bg="white"
      cursor="pointer"
      onClick={() => navigate(`/trips/${trip.id}`)}
      _hover={{ shadow: 'lg' }}
    >
      <Flex justify="space-between" align="center" mb={2}>
        <Heading size="md">{trip.title}</Heading>
        <Badge colorScheme={getStatusColor(trip.status)}>{trip.status}</Badge>
      </Flex>
      <Text color="gray.600" mb={2}>
        {trip.destination}
      </Text>
      <Text fontSize="sm" color="gray.500">
        {format(new Date(trip.start_date), 'MMM d, yyyy')} -{' '}
        {format(new Date(trip.end_date), 'MMM d, yyyy')}
      </Text>
      {trip.budget && (
        <Text fontSize="sm" color="gray.500" mt={2}>
          Budget: {trip.budget.currency} {trip.budget.total.toLocaleString()}
        </Text>
      )}
    </Box>
  );

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg">My Trips</Heading>
        <Button colorScheme="blue" onClick={() => navigate('/trips/new')}>
          Plan New Trip
        </Button>
      </Flex>

      <Flex mb={4}>
        <Select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          placeholder="Filter by status"
          maxW="200px"
        >
          <option value="PLANNING">Planning</option>
          <option value="BOOKED">Booked</option>
          <option value="COMPLETED">Completed</option>
        </Select>
      </Flex>

      {isLoading ? (
        <Text>Loading trips...</Text>
      ) : (
        <>
          <Grid
            templateColumns="repeat(auto-fill, minmax(300px, 1fr))"
            gap={6}
            mb={6}
          >
            {data?.trips.map((trip) => (
              <TripCard key={trip.id} trip={trip} />
            ))}
          </Grid>

          {data && data.total > 0 && (
            <Flex justify="center" gap={2}>
              <Button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                isDisabled={page === 1}
              >
                Previous
              </Button>
              <Button
                onClick={() => setPage((p) => p + 1)}
                isDisabled={page * 10 >= data.total}
              >
                Next
              </Button>
            </Flex>
          )}

          {data?.total === 0 && (
            <Box textAlign="center" py={10}>
              <Text fontSize="lg" mb={4}>
                No trips found
              </Text>
              <Button
                colorScheme="blue"
                onClick={() => navigate('/trips/new')}
              >
                Plan Your First Trip
              </Button>
            </Box>
          )}
        </>
      )}
    </Box>
  );
};

export default TripList; 