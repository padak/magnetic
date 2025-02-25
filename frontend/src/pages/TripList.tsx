import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Button,
  Flex,
  Grid,
  Heading,
  Text,
  Select,
  Badge,
  VStack,
  HStack,
  Icon,
  useToast
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { tripService } from '../api/tripService';
import { Trip } from '../types/trip';
import { FaMapMarkerAlt, FaCalendarAlt, FaMoneyBillWave } from 'react-icons/fa';
import { Link as RouterLink } from 'react-router-dom';

const TripList = () => {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string>('');
  const navigate = useNavigate();
  const toast = useToast();

  const { data, isLoading, error } = useQuery({
    queryKey: ['trips', page, status],
    queryFn: () => tripService.listTrips(page, 10, status),
  });

  useEffect(() => {
    if (error) {
      toast({
        title: 'Error loading trips',
        description: error instanceof Error ? error.message : 'An error occurred',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  }, [error, toast]);

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
    <Box p={5} shadow="md" borderWidth="1px" borderRadius="lg">
      <VStack align="stretch" spacing={3}>
        <HStack justify="space-between">
          <Heading size="md">{trip.title}</Heading>
          <Badge colorScheme={getStatusColor(trip.status)}>
            {trip.status}
          </Badge>
        </HStack>
        
        <Text color="gray.600">{trip.description}</Text>
        
        <HStack>
          <Icon as={FaMapMarkerAlt} color="blue.500" />
          <Text>{trip.destination}</Text>
        </HStack>
        
        <HStack>
          <Icon as={FaCalendarAlt} color="green.500" />
          <Text>
            {new Date(trip.start_date).toLocaleDateString()} - {new Date(trip.end_date).toLocaleDateString()}
          </Text>
        </HStack>
        
        {trip.budget?.total && trip.budget?.currency && (
          <HStack>
            <Icon as={FaMoneyBillWave} color="purple.500" />
            <Text>
              Budget: {trip.budget.currency} {trip.budget.total.toLocaleString()}
            </Text>
          </HStack>
        )}
        
        <Button 
          as={RouterLink} 
          to={`/trips/${trip.id}`}
          size="sm" 
          colorScheme="blue"
        >
          View Details
        </Button>
      </VStack>
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
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setStatus(e.target.value)}
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
                disabled={page === 1}
              >
                Previous
              </Button>
              <Button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * 10 >= data.total}
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