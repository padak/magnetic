import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Chip,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  CircularProgress,
  Divider,
  Alert,
} from '@mui/material';
import { format } from 'date-fns';
import { tripApi } from '../api/client';
import { Trip, Activity, Accommodation } from '../types/trip';

const TripDetails = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const {
    data: trip,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['trip', id],
    queryFn: () => tripApi.getTrip(Number(id)),
  });

  const deleteMutation = useMutation({
    mutationFn: tripApi.deleteTrip,
    onSuccess: () => {
      navigate('/');
    },
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box textAlign="center" py={4}>
        <Alert severity="error">Error loading trip details. Please try again later.</Alert>
      </Box>
    );
  }

  if (!trip) {
    return (
      <Box textAlign="center" py={4}>
        <Alert severity="warning">Trip not found.</Alert>
      </Box>
    );
  }

  const handleDelete = () => {
    deleteMutation.mutate(trip.id);
    setDeleteDialogOpen(false);
  };

  const renderActivity = (activity: Activity) => (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="h6">{activity.name}</Typography>
        {activity.description && (
          <Typography color="text.secondary" paragraph>
            {activity.description}
          </Typography>
        )}
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2">
              Time: {format(new Date(activity.start_time), 'h:mm a')} -{' '}
              {format(new Date(activity.end_time), 'h:mm a')}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2">Cost: ${activity.cost}</Typography>
          </Grid>
          {activity.location && (
            <Grid item xs={12}>
              <Typography variant="body2">Location: {activity.location}</Typography>
            </Grid>
          )}
        </Grid>
      </CardContent>
    </Card>
  );

  const renderAccommodation = (accommodation: Accommodation) => (
    <Card variant="outlined" sx={{ mb: 2, bgcolor: 'background.default' }}>
      <CardContent>
        <Typography variant="h6">Accommodation</Typography>
        <Typography variant="subtitle1">{accommodation.name}</Typography>
        <Typography color="text.secondary">{accommodation.address}</Typography>
        <Typography variant="body2" sx={{ mt: 1 }}>
          Check-in: {format(new Date(accommodation.check_in), 'MMM d, yyyy h:mm a')}
        </Typography>
        <Typography variant="body2">
          Check-out: {format(new Date(accommodation.check_out), 'MMM d, yyyy h:mm a')}
        </Typography>
        <Typography variant="body2" sx={{ mt: 1 }}>
          Cost: ${accommodation.cost}
        </Typography>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={4}
        flexWrap="wrap"
        gap={2}
      >
        <Box>
          <Typography variant="h4" component="h1">
            {trip.title}
          </Typography>
          <Typography color="text.secondary" variant="h6">
            {trip.destination}
          </Typography>
        </Box>
        <Box>
          <Chip
            label={trip.status}
            color={
              trip.status === 'PLANNING'
                ? 'primary'
                : trip.status === 'COMPLETED'
                ? 'success'
                : 'default'
            }
            sx={{ mr: 1 }}
          />
          <Button
            variant="outlined"
            color="error"
            onClick={() => setDeleteDialogOpen(true)}
          >
            Delete Trip
          </Button>
        </Box>
      </Box>

      <Grid container spacing={4}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                Itinerary
              </Typography>
              {trip.itinerary_days.map((day, index) => (
                <Box key={index} mb={4}>
                  <Typography variant="h6" gutterBottom>
                    Day {index + 1} - {format(new Date(day.date), 'EEEE, MMMM d, yyyy')}
                  </Typography>
                  {day.activities.map((activity, actIndex) => (
                    <Box key={actIndex} mb={2}>
                      {renderActivity(activity)}
                    </Box>
                  ))}
                  {day.accommodation && renderAccommodation(day.accommodation)}
                  {index < trip.itinerary_days.length - 1 && (
                    <Divider sx={{ my: 3 }} />
                  )}
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                Trip Details
              </Typography>
              <Typography variant="body1" paragraph>
                {trip.description}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                Dates
              </Typography>
              <Typography variant="body2" paragraph>
                {format(new Date(trip.start_date), 'MMM d, yyyy')} -{' '}
                {format(new Date(trip.end_date), 'MMM d, yyyy')}
              </Typography>

              {trip.budget && (
                <>
                  <Typography variant="subtitle1" gutterBottom>
                    Budget
                  </Typography>
                  <Typography variant="body2">
                    Total Budget: ${trip.budget.total}
                  </Typography>
                  <Typography variant="body2">
                    Spent: ${trip.budget.spent}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Currency: {trip.budget.currency}
                  </Typography>
                </>
              )}

              <Typography variant="subtitle1" sx={{ mt: 2 }} gutterBottom>
                Preferences
              </Typography>
              <Typography variant="body2">
                Adults: {trip.preferences.adults}
              </Typography>
              <Typography variant="body2">
                Children: {trip.preferences.children}
              </Typography>
              <Typography variant="body2">
                Hotel Budget: {trip.preferences.hotel_budget}
              </Typography>
              <Typography variant="body2">
                Max Activity Price: ${trip.preferences.max_activity_price}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        aria-labelledby="delete-dialog-title"
      >
        <DialogTitle id="delete-dialog-title">Delete Trip</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this trip? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDelete} color="error" autoFocus>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TripDetails; 