import {
  Box,
  Button,
  Container,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Textarea,
  useToast,
  VStack,
} from "@chakra-ui/react";
import { useMutation } from "@tanstack/react-query";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { useTransition } from 'react';

interface TripFormData {
  title: string;
  description: string;
  destination: string;
  start_date: string;
  end_date: string;
}

export default function CreateTrip() {
  const navigate = useNavigate();
  const toast = useToast();
  const [isPending, startTransition] = useTransition();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<TripFormData>();

  const createTripMutation = useMutation({
    mutationFn: async (data: TripFormData) => {
      const response = await axios.post("/api/trips", data);
      return response.data;
    },
    onSuccess: (data) => {
      toast({
        title: "Trip created successfully",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      startTransition(() => {
        navigate(`/trips/${data.id}`);
      });
    },
    onError: () => {
      toast({
        title: "Error creating trip",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    },
  });

  const onSubmit = (data: TripFormData) => {
    createTripMutation.mutate(data);
  };

  return (
    <Container maxW="container.md" py={8}>
      <Heading mb={6}>Create New Trip</Heading>
      <Box as="form" onSubmit={handleSubmit(onSubmit)}>
        <VStack spacing={4} align="stretch">
          <FormControl isRequired>
            <FormLabel>Title</FormLabel>
            <Input
              {...register("title", { required: "Title is required" })}
              placeholder="Enter trip title"
            />
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Destination</FormLabel>
            <Input
              {...register("destination", { required: "Destination is required" })}
              placeholder="Enter destination"
            />
          </FormControl>

          <FormControl>
            <FormLabel>Description</FormLabel>
            <Textarea
              {...register("description")}
              placeholder="Enter trip description"
            />
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Start Date</FormLabel>
            <Input
              {...register("start_date", { required: "Start date is required" })}
              type="date"
            />
          </FormControl>

          <FormControl isRequired>
            <FormLabel>End Date</FormLabel>
            <Input
              {...register("end_date", { required: "End date is required" })}
              type="date"
            />
          </FormControl>

          <Button
            mt={4}
            colorScheme="blue"
            isLoading={isSubmitting || isPending}
            type="submit"
            width="full"
          >
            Create Trip
          </Button>
        </VStack>
      </Box>
    </Container>
  );
} 