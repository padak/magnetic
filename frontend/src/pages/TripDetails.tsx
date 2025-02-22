import {
  Box,
  Container,
  Heading,
  Spinner,
  Text,
  VStack,
  HStack,
  Badge,
  Button,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useToast,
  Link,
  Alert,
  AlertIcon,
} from "@chakra-ui/react";
import { useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from 'react';
import { tripService } from "../api/tripService";
import { Trip, TripDocument, TripMonitoring } from "../types/trip";

export default function TripDetails() {
  const { id } = useParams<{ id: string }>();
  const toast = useToast();
  const queryClient = useQueryClient();

  // Fetch trip details
  const { data: trip, isLoading: tripLoading } = useQuery<Trip>({
    queryKey: ["trip", id],
    queryFn: () => tripService.getTrip(Number(id)),
  });

  // Fetch trip documents
  const { data: documents, isLoading: docsLoading } = useQuery<TripDocument[]>({
    queryKey: ["trip-documents", id],
    queryFn: () => tripService.getTripDocuments(Number(id)),
    enabled: !!trip,
  });

  // Fetch monitoring updates
  const { data: monitoring, isLoading: monitoringLoading } = useQuery<TripMonitoring>({
    queryKey: ["trip-monitoring", id],
    queryFn: () => tripService.getMonitoringUpdates(Number(id)),
    enabled: !!trip && trip.status === "in_progress",
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Start monitoring when trip starts
  useEffect(() => {
    if (trip?.status === "in_progress") {
      tripService.startMonitoring(Number(id), ["weather", "travel"]);
    }
    return () => {
      if (trip?.status === "completed") {
        tripService.stopMonitoring(Number(id));
      }
    };
  }, [id, trip?.status]);

  if (tripLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minH="60vh">
        <Spinner size="xl" />
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case "planning":
        return "blue";
      case "planned":
        return "green";
      case "in_progress":
        return "orange";
      case "completed":
        return "gray";
      default:
        return "gray";
    }
  };

  return (
    <Container maxW="container.lg" py={8}>
      <VStack spacing={6} align="stretch">
        <HStack justify="space-between">
          <Heading>{trip.title}</Heading>
          <Badge colorScheme={getStatusColor(trip.status)} fontSize="lg">
            {trip.status}
          </Badge>
        </HStack>

        <Tabs>
          <TabList>
            <Tab>Overview</Tab>
            <Tab>Documents</Tab>
            {trip.status === "in_progress" && <Tab>Live Updates</Tab>}
          </TabList>

          <TabPanels>
            <TabPanel>
              <VStack spacing={4} align="stretch">
                <Box>
                  <Text fontSize="lg" fontWeight="bold">Destination</Text>
                  <Text>{trip.destination}</Text>
                </Box>

                <Box>
                  <Text fontSize="lg" fontWeight="bold">Description</Text>
                  <Text>{trip.description}</Text>
                </Box>

                <Box>
                  <Text fontSize="lg" fontWeight="bold">Dates</Text>
                  <Text>
                    {new Date(trip.start_date).toLocaleDateString()} - {new Date(trip.end_date).toLocaleDateString()}
                  </Text>
                </Box>

                <Box>
                  <Text fontSize="lg" fontWeight="bold">Preferences</Text>
                  <VStack align="stretch" spacing={2}>
                    <Text>Budget: {trip.preferences.budget}</Text>
                    <Text>Interests: {trip.preferences.interests.join(", ")}</Text>
                    {trip.preferences.accommodation_type && (
                      <Text>Accommodation: {trip.preferences.accommodation_type}</Text>
                    )}
                    {trip.preferences.travel_style && (
                      <Text>Travel Style: {trip.preferences.travel_style}</Text>
                    )}
                  </VStack>
                </Box>
              </VStack>
            </TabPanel>

            <TabPanel>
              {docsLoading ? (
                <Spinner />
              ) : documents?.length ? (
                <VStack spacing={4} align="stretch">
                  {documents.map((doc) => (
                    <Box key={doc.path} p={4} borderWidth={1} borderRadius="md">
                      <HStack justify="space-between">
                        <VStack align="start" spacing={1}>
                          <Text fontWeight="bold">
                            {doc.type.charAt(0).toUpperCase() + doc.type.slice(1)}
                          </Text>
                          <Text fontSize="sm" color="gray.500">
                            Last updated: {new Date(doc.last_updated).toLocaleString()}
                          </Text>
                        </VStack>
                        <Link href={doc.path} isExternal>
                          <Button size="sm">View</Button>
                        </Link>
                      </HStack>
                    </Box>
                  ))}
                </VStack>
              ) : (
                <Text>No documents available</Text>
              )}
            </TabPanel>

            {trip.status === "in_progress" && (
              <TabPanel>
                {monitoringLoading ? (
                  <Spinner />
                ) : monitoring ? (
                  <VStack spacing={6} align="stretch">
                    <Box>
                      <Heading size="md" mb={4}>Weather Updates</Heading>
                      <VStack spacing={3} align="stretch">
                        {monitoring.weather_updates.map((update, index) => (
                          <Box key={index} p={3} borderWidth={1} borderRadius="md">
                            <Text fontWeight="bold">
                              Temperature: {update.temperature}°C
                            </Text>
                            <Text>Conditions: {update.conditions}</Text>
                            <Text fontSize="sm" color="gray.500">
                              {new Date(update.timestamp).toLocaleString()}
                            </Text>
                          </Box>
                        ))}
                      </VStack>
                    </Box>

                    {monitoring.travel_alerts && monitoring.travel_alerts.length > 0 && (
                      <Box>
                        <Heading size="md" mb={4}>Travel Alerts</Heading>
                        <VStack spacing={3} align="stretch">
                          {monitoring.travel_alerts.map((alert, index) => (
                            <Alert
                              key={index}
                              status={alert.severity === 'critical' ? 'error' : alert.severity === 'warning' ? 'warning' : 'info'}
                            >
                              <AlertIcon />
                              <VStack align="start" spacing={1}>
                                <Text fontWeight="bold">{alert.type}</Text>
                                <Text>{alert.message}</Text>
                                <Text fontSize="sm">
                                  {new Date(alert.timestamp).toLocaleString()}
                                </Text>
                              </VStack>
                            </Alert>
                          ))}
                        </VStack>
                      </Box>
                    )}
                  </VStack>
                ) : (
                  <Text>No monitoring data available</Text>
                )}
              </TabPanel>
            )}
          </TabPanels>
        </Tabs>
      </VStack>
    </Container>
  );
} 