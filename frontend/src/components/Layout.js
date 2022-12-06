import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  AppBar,
  Box,
  Button,
  Container,
  Link,
  Toolbar,
  Typography,
  useTheme,
} from '@mui/material';
import SecurityIcon from '@mui/icons-material/Security';
import DashboardIcon from '@mui/icons-material/Dashboard';
import AnalyticsIcon from '@mui/icons-material/Analytics';

const Layout = ({ children }) => {
  const theme = useTheme();

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <SecurityIcon sx={{ mr: 2 }} />
          <Link
            component={RouterLink}
            to="/"
            sx={{ textDecoration: 'none', color: 'inherit', flexGrow: 1 }}
          >
            <Typography variant="h6" component="div">
              PhishGuard
            </Typography>
          </Link>
          
          <Button
            color="inherit"
            component={RouterLink}
            to="/"
            startIcon={<DashboardIcon />}
            sx={{ mr: 2 }}
          >
            Analyze
          </Button>
          
          <Button
            color="inherit"
            component={RouterLink}
            to="/history"
            startIcon={<AnalyticsIcon />}
          >
            History
          </Button>
        </Toolbar>
      </AppBar>

      <Container
        component="main"
        maxWidth="lg"
        sx={{
          mt: 4,
          mb: 4,
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {children}
      </Container>

      <Box
        component="footer"
        sx={{
          py: 3,
          px: 2,
          mt: 'auto',
          backgroundColor: theme.palette.grey[100],
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="body2" color="text.secondary" align="center">
            PhishGuard - Email Phishing Analysis Tool © {new Date().getFullYear()}
          </Typography>
        </Container>
      </Box>
    </Box>
  );
};

export default Layout; 