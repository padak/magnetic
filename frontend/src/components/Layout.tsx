import { Box, Container, Flex, Heading, Link as ChakraLink } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
  return (
    <Box minH="100vh" bg="gray.50">
      <Box bg="blue.600" color="white" py={4} mb={8}>
        <Container maxW="container.xl">
          <Flex justify="space-between" align="center">
            <ChakraLink as={RouterLink} to="/" _hover={{ textDecoration: 'none' }}>
              <Heading size="lg">US Family Trip Planner</Heading>
            </ChakraLink>
            <Flex gap={4}>
              <ChakraLink as={RouterLink} to="/" _hover={{ color: 'blue.200' }}>
                My Trips
              </ChakraLink>
              <ChakraLink as={RouterLink} to="/trips/new" _hover={{ color: 'blue.200' }}>
                Plan New Trip
              </ChakraLink>
            </Flex>
          </Flex>
        </Container>
      </Box>
      <Container maxW="container.xl" pb={8}>
        {children}
      </Container>
    </Box>
  );
};

export default Layout; 