import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers';
import { tripApi } from '../api/client';
import { TripCreate, TripPreferences } from '../types/trip';

const defaultPreferences: TripPreferences = {
  adults: 2,
  children: 0,
  hotel_budget: 'MODERATE',
  max_activity_price: 100,
  activity_types: ['SIGHTSEEING', 'FAMILY_FUN'],
  family_friendly: true,
  accessible: false,
  transportation_budget: 500,
  food_budget: 300,
  misc_budget: 200,
  currency: 'USD',
};

interface FormData extends Omit<TripCreate, 'start_date' | 'end_date'> {
  preferences: TripPreferences;
}

const CreateTrip = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<Partial<FormData>>({
    preferences: defaultPreferences,
  });
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const createTripMutation = useMutation({
    mutationFn: tripApi.createTrip,
    onSuccess: (data) => {
      navigate(`/trips/${data.id}`);
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title || !formData.destination || !startDate || !endDate) {
      setError('Please fill in all required fields');
      return;
    }

    const tripData: TripCreate = {
      title: formData.title,
      destination: formData.destination,
      description: formData.description,
      start_date: startDate.toISOString(),
      end_date: endDate.toISOString(),
      preferences: formData.preferences || defaultPreferences,
    };

    createTripMutation.mutate(tripData);
  };

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handlePreferenceChange = (field: keyof TripPreferences, value: number | string | boolean) => {
    setFormData((prev) => ({
      ...prev,
      preferences: {
        ...(prev.preferences || defaultPreferences),
        [field]: value,
      },
    }));
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Plan New Trip
      </Typography>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  label="Trip Title"
                  value={formData.title || ''}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Description"
                  multiline
                  rows={3}
                  value={formData.description || ''}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  label="Destination"
                  value={formData.destination || ''}
                  onChange={(e) => handleInputChange('destination', e.target.value)}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <DatePicker
                  label="Start Date"
                  value={startDate}
                  onChange={(date) => setStartDate(date)}
                  slotProps={{
                    textField: { fullWidth: true, required: true },
                  }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <DatePicker
                  label="End Date"
                  value={endDate}
                  onChange={(date) => setEndDate(date)}
                  slotProps={{
                    textField: { fullWidth: true, required: true },
                  }}
                  minDate={startDate || undefined}
                />
              </Grid>

              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Trip Preferences
                </Typography>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  type="number"
                  fullWidth
                  label="Number of Adults"
                  value={formData.preferences?.adults || 2}
                  onChange={(e) =>
                    handlePreferenceChange('adults', parseInt(e.target.value))
                  }
                  inputProps={{ min: 1 }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  type="number"
                  fullWidth
                  label="Number of Children"
                  value={formData.preferences?.children || 0}
                  onChange={(e) =>
                    handlePreferenceChange('children', parseInt(e.target.value))
                  }
                  inputProps={{ min: 0 }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Hotel Budget</InputLabel>
                  <Select
                    value={formData.preferences?.hotel_budget || 'MODERATE'}
                    onChange={(e) =>
                      handlePreferenceChange('hotel_budget', e.target.value)
                    }
                    label="Hotel Budget"
                  >
                    <MenuItem value="BUDGET">Budget</MenuItem>
                    <MenuItem value="MODERATE">Moderate</MenuItem>
                    <MenuItem value="LUXURY">Luxury</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  type="number"
                  fullWidth
                  label="Max Activity Price"
                  value={formData.preferences?.max_activity_price || 100}
                  onChange={(e) =>
                    handlePreferenceChange(
                      'max_activity_price',
                      parseFloat(e.target.value)
                    )
                  }
                  InputProps={{
                    startAdornment: '$',
                  }}
                />
              </Grid>
            </Grid>

            {error && (
              <Box mt={2}>
                <Alert severity="error">{error}</Alert>
              </Box>
            )}

            <Box mt={3} display="flex" justifyContent="flex-end">
              <Button
                type="submit"
                variant="contained"
                color="primary"
                size="large"
                disabled={createTripMutation.isPending}
              >
                {createTripMutation.isPending ? 'Creating...' : 'Create Trip'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      </form>
    </Box>
  );
};

export default CreateTrip; 