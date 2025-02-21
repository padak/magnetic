import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Pagination,
  Chip,
  Link,
  CircularProgress,
} from '@mui/material';
import { format } from 'date-fns';
import { tripApi } from '../api/client';
import { Trip } from '../types/trip';

const TripList = () => {
  const [page, setPage] = useState(1);
  const pageSize = 9;

  const { data, isLoading, error } = useQuery({
    queryKey: ['trips', page],
    queryFn: () => tripApi.listTrips(page, pageSize),
  });

  const handlePageChange = (_: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

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
        <Typography color="error">
          Error loading trips. Please try again later.
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1">
          Your Trips
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {data?.trips.map((trip: Trip) => (
          <Grid item xs={12} sm={6} md={4} key={trip.id}>
            <Card>
              <CardContent>
                <Link
                  component={RouterLink}
                  to={`/trips/${trip.id}`}
                  color="inherit"
                  underline="none"
                >
                  <Typography variant="h6" gutterBottom>
                    {trip.title}
                  </Typography>
                </Link>
                <Typography color="text.secondary" gutterBottom>
                  {trip.destination}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {format(new Date(trip.start_date), 'MMM d, yyyy')} -{' '}
                  {format(new Date(trip.end_date), 'MMM d, yyyy')}
                </Typography>
                <Box mt={1}>
                  <Chip
                    label={trip.status}
                    color={
                      trip.status === 'PLANNING'
                        ? 'primary'
                        : trip.status === 'COMPLETED'
                        ? 'success'
                        : 'default'
                    }
                    size="small"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {data && data.total > pageSize && (
        <Box display="flex" justifyContent="center" mt={4}>
          <Pagination
            count={Math.ceil(data.total / pageSize)}
            page={page}
            onChange={handlePageChange}
            color="primary"
          />
        </Box>
      )}
    </Box>
  );
};

export default TripList; 