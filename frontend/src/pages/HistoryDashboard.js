import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Typography,
  Alert,
} from '@mui/material';
import {
  Download,
  Assessment,
  Warning,
  CheckCircle,
  Error,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { format } from 'date-fns';
import axios from 'axios';

const COLORS = {
  high: '#d32f2f',
  medium: '#f57c00',
  low: '#388e3c',
  unknown: '#757575'
};

const HistoryDashboard = () => {
  // State management
  const [statistics, setStatistics] = useState(null);
  const [trends, setTrends] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Pagination and filtering
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalCount, setTotalCount] = useState(0);
  const [filters, setFilters] = useState({
    riskLevel: '',
    dateFrom: '',
    dateTo: ''
  });
  
  // Chart period
  const [trendPeriod, setTrendPeriod] = useState(30);

  useEffect(() => {
    loadDashboardData();
  }, []);

  useEffect(() => {
    loadHistory();
  }, [page, rowsPerPage, filters]);

  useEffect(() => {
    loadTrends();
  }, [trendPeriod]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [statsResponse, trendsResponse] = await Promise.all([
        axios.get('/api/statistics'),
        axios.get(`/api/trends?days=${trendPeriod}`)
      ]);
      
      setStatistics(statsResponse.data);
      setTrends(trendsResponse.data);
      setError(null);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Error loading dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const params = new URLSearchParams({
        page: page + 1,
        per_page: rowsPerPage
      });
      
      if (filters.riskLevel) params.append('risk_level', filters.riskLevel);
      if (filters.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters.dateTo) params.append('date_to', filters.dateTo);
      
      const response = await axios.get(`/api/history?${params}`);
      setHistory(response.data.results);
      setTotalCount(response.data.total);
    } catch (err) {
      console.error('Error loading history:', err);
    }
  };

  const loadTrends = async () => {
    try {
      const response = await axios.get(`/api/trends?days=${trendPeriod}`);
      setTrends(response.data);
    } catch (err) {
      console.error('Error loading trends:', err);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPage(0); // Reset to first page when filtering
  };

  const handleExport = async (format) => {
    try {
      const params = new URLSearchParams({ format });
      if (filters.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters.dateTo) params.append('date_to', filters.dateTo);
      
      const response = await axios.get(`/api/export?${params}`, {
        responseType: format === 'csv' ? 'blob' : 'json'
      });
      
      if (format === 'csv') {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `phishguard_export_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        link.remove();
      } else {
        const dataStr = JSON.stringify(response.data, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `phishguard_export_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
      }
    } catch (err) {
      console.error('Error exporting data:', err);
      alert('Failed to export data');
    }
  };

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const formatDate = (dateString) => {
    return format(new Date(dateString), 'MMM dd, yyyy HH:mm');
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  const pieData = statistics ? [
    { name: 'High Risk', value: statistics.risk_distribution.high, color: COLORS.high },
    { name: 'Medium Risk', value: statistics.risk_distribution.medium, color: COLORS.medium },
    { name: 'Low Risk', value: statistics.risk_distribution.low, color: COLORS.low }
  ] : [];

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Historical Analysis Dashboard
      </Typography>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Assessment sx={{ mr: 2, color: 'primary.main' }} />
                <Box>
                  <Typography variant="h4">
                    {statistics?.total_analyses || 0}
                  </Typography>
                  <Typography color="text.secondary">
                    Total Analyses
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Error sx={{ mr: 2, color: 'error.main' }} />
                <Box>
                  <Typography variant="h4">
                    {statistics?.risk_distribution.high || 0}
                  </Typography>
                  <Typography color="text.secondary">
                    High Risk
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Warning sx={{ mr: 2, color: 'warning.main' }} />
                <Box>
                  <Typography variant="h4">
                    {statistics?.risk_distribution.medium || 0}
                  </Typography>
                  <Typography color="text.secondary">
                    Medium Risk
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckCircle sx={{ mr: 2, color: 'success.main' }} />
                <Box>
                  <Typography variant="h4">
                    {statistics?.risk_distribution.low || 0}
                  </Typography>
                  <Typography color="text.secondary">
                    Low Risk
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Trend Chart */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">
                  Analysis Trends
                </Typography>
                <FormControl size="small">
                  <InputLabel>Period</InputLabel>
                  <Select
                    value={trendPeriod}
                    onChange={(e) => setTrendPeriod(e.target.value)}
                    label="Period"
                  >
                    <MenuItem value={7}>7 Days</MenuItem>
                    <MenuItem value={30}>30 Days</MenuItem>
                    <MenuItem value={90}>90 Days</MenuItem>
                  </Select>
                </FormControl>
              </Box>
              
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trends?.trend_data || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="total_analyses" stroke="#1976d2" name="Total" />
                  <Line type="monotone" dataKey="high_risk" stroke="#d32f2f" name="High Risk" />
                  <Line type="monotone" dataKey="medium_risk" stroke="#f57c00" name="Medium Risk" />
                  <Line type="monotone" dataKey="low_risk" stroke="#388e3c" name="Low Risk" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Risk Distribution Pie Chart */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Risk Distribution
              </Typography>
              
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* History Table */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">
              Analysis History
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                startIcon={<Download />}
                onClick={() => handleExport('csv')}
              >
                Export CSV
              </Button>
              <Button
                startIcon={<Download />}
                onClick={() => handleExport('json')}
              >
                Export JSON
              </Button>
            </Box>
          </Box>

          {/* Filters */}
          <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Risk Level</InputLabel>
              <Select
                value={filters.riskLevel}
                onChange={(e) => handleFilterChange('riskLevel', e.target.value)}
                label="Risk Level"
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="low">Low</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              size="small"
              label="From Date"
              type="date"
              value={filters.dateFrom}
              onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
            
            <TextField
              size="small"
              label="To Date"
              type="date"
              value={filters.dateTo}
              onChange={(e) => handleFilterChange('dateTo', e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Subject</TableCell>
                  <TableCell>Sender</TableCell>
                  <TableCell>Risk Level</TableCell>
                  <TableCell>Threat Score</TableCell>
                  <TableCell>Type</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {history.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>
                      {formatDate(row.created_at)}
                    </TableCell>
                    <TableCell>
                      {row.subject || 'N/A'}
                    </TableCell>
                    <TableCell>
                      {row.sender || 'N/A'}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={row.risk_level.toUpperCase()}
                        color={getRiskColor(row.risk_level)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {(row.threat_score * 100).toFixed(1)}%
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={row.analysis_type.toUpperCase()}
                        variant="outlined"
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={totalCount}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={(event, newPage) => setPage(newPage)}
            onRowsPerPageChange={(event) => {
              setRowsPerPage(parseInt(event.target.value, 10));
              setPage(0);
            }}
          />
        </CardContent>
      </Card>
    </Box>
  );
};

export default HistoryDashboard; 