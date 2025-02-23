import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Heading,
  Select,
  NumberInput,
  NumberInputField,
  Checkbox,
  useToast,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';
import { tripService } from '../api/tripService';
import { TripCreate } from '../types/trip';

type FormData = TripCreate;

const CreateTrip = () => {
  const { register, handleSubmit } = useForm<FormData>();
  const navigate = useNavigate();
  const toast = useToast();

  const onSubmit = async (data: FormData) => {
    try {
      const response = await tripService.createTrip({
        ...data,
        preferences: {
          interests: ['History', 'Culture'],
          budget: 'MODERATE',
          activity_types: ['SIGHTSEEING', 'FAMILY_FUN', 'HISTORY', 'CULTURE'],
          adults: data.preferences.adults,
          children: data.preferences.children,
          hotel_budget: data.preferences.hotel_budget,
          max_activity_price: data.preferences.max_activity_price,
          family_friendly: data.preferences.family_friendly,
          accessible: data.preferences.accessible,
          transportation_budget: data.preferences.transportation_budget,
          food_budget: data.preferences.food_budget,
          misc_budget: data.preferences.misc_budget,
          currency: data.preferences.currency
        },
      });
      
      toast({
        title: 'Trip created successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      
      navigate(`/trips/${response.id}`);
    } catch (error) {
      toast({
        title: 'Error creating trip',
        description: error instanceof Error ? error.message : 'An unexpected error occurred',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  return (
    <Box maxW="800px" mx="auto" py={8} px={4}>
      <Heading mb={6}>Create New Trip</Heading>
      <form onSubmit={handleSubmit(onSubmit)}>
        <VStack spacing={4} align="stretch">
          <FormControl isRequired>
            <FormLabel>Title</FormLabel>
            <Input {...register('title')} />
          </FormControl>

          <FormControl>
            <FormLabel>Description</FormLabel>
            <Input {...register('description')} />
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Destination</FormLabel>
            <Input {...register('destination')} />
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Start Date</FormLabel>
            <Input type="date" {...register('start_date')} />
          </FormControl>

          <FormControl isRequired>
            <FormLabel>End Date</FormLabel>
            <Input type="date" {...register('end_date')} />
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Number of Adults</FormLabel>
            <NumberInput min={1}>
              <NumberInputField {...register('preferences.adults')} />
            </NumberInput>
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Number of Children</FormLabel>
            <NumberInput min={0}>
              <NumberInputField {...register('preferences.children')} />
            </NumberInput>
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Hotel Budget</FormLabel>
            <Select {...register('preferences.hotel_budget')}>
              <option value="BUDGET">Budget</option>
              <option value="MODERATE">Moderate</option>
              <option value="LUXURY">Luxury</option>
            </Select>
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Max Activity Price</FormLabel>
            <NumberInput min={0}>
              <NumberInputField {...register('preferences.max_activity_price')} />
            </NumberInput>
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Transportation Budget</FormLabel>
            <NumberInput min={0}>
              <NumberInputField {...register('preferences.transportation_budget')} />
            </NumberInput>
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Food Budget</FormLabel>
            <NumberInput min={0}>
              <NumberInputField {...register('preferences.food_budget')} />
            </NumberInput>
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Miscellaneous Budget</FormLabel>
            <NumberInput min={0}>
              <NumberInputField {...register('preferences.misc_budget')} />
            </NumberInput>
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Currency</FormLabel>
            <Select {...register('preferences.currency')}>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="GBP">GBP</option>
            </Select>
          </FormControl>

          <FormControl>
            <Checkbox {...register('preferences.family_friendly')}>
              Family Friendly
            </Checkbox>
          </FormControl>

          <FormControl>
            <Checkbox {...register('preferences.accessible')}>
              Accessible
            </Checkbox>
          </FormControl>

          <Button type="submit" colorScheme="blue" size="lg">
            Create Trip
          </Button>
        </VStack>
      </form>
    </Box>
  );
};

export default CreateTrip; 