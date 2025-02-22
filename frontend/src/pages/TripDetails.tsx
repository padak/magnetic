import { Box, Container, Heading, Spinner, Text } from "@chakra-ui/react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useTransition } from 'react';

interface Trip {
  id: number;
  title: string;
  description: string;
  destination: string;
  start_date: string;
  end_date: string;
  status: string;
  preferences: Record<string, any>;
}

export default function TripDetails() {
  const { id } = useParams<{ id: string }>();
  const [isPending, startTransition] = useTransition();

  const { data: trip, isLoading, error } = useQuery<Trip>({
    queryKey: ["trip", id],
    queryFn: async () => {
      const response = await axios.get(`/api/trips/${id}`);
      return response.data;
    },
  });

  if (isLoading || isPending) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minH="60vh">
        <Spinner size="xl" />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={4}>
        <Text color="red.500">Error loading trip details</Text>
      </Box>
    );
  }

  if (!trip) {
    return (
      <Box p={4}>
        <Text>Trip not found</Text>
      </Box>
    );
  }

  return (
    <Container maxW="container.lg" py={8}>
      <Heading mb={6}>{trip.title}</Heading>
      <Box mb={4}>
        <Text fontSize="lg" fontWeight="bold">Destination</Text>
        <Text>{trip.destination}</Text>
      </Box>
      <Box mb={4}>
        <Text fontSize="lg" fontWeight="bold">Description</Text>
        <Text>{trip.description}</Text>
      </Box>
      <Box mb={4}>
        <Text fontSize="lg" fontWeight="bold">Dates</Text>
        <Text>
          {new Date(trip.start_date).toLocaleDateString()} - {new Date(trip.end_date).toLocaleDateString()}
        </Text>
      </Box>
      <Box mb={4}>
        <Text fontSize="lg" fontWeight="bold">Status</Text>
        <Text>{trip.status}</Text>
      </Box>
    </Container>
  );
} 