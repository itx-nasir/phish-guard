import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Alert,
  Button,
  List,
  ListItem,
  Chip,
  Divider,
} from '@mui/material';
import { Download, Error, CheckCircle, Refresh } from '@mui/icons-material';
import axios from 'axios';
import { API_ENDPOINTS } from '../utils/constants';

const BatchAnalysisResult = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState({});
  
  const taskIds = location.state?.taskIds || [];

  useEffect(() => {
    if (!location.state?.taskIds) {
      navigate('/');
      return;
    }

    const fetchResults = async () => {
      const newResults = { ...results };
      let allCompleted = true;

      for (const { task_id, filename } of taskIds) {
        if (!newResults[task_id] || newResults[task_id].status === 'processing') {
          try {
            const response = await axios.get(API_ENDPOINTS.ANALYSIS_RESULT(task_id));
            newResults[task_id] = {
              ...response.data,
              filename,
              status: response.data.status || 'processing'
            };

            if (response.data.progress !== undefined) {
              setProgress(prev => ({
                ...prev,
                [task_id]: response.data.progress
              }));
            }

            if (response.data.status === 'processing') {
              allCompleted = false;
            }
          } catch (err) {
            console.error(`Error fetching results for ${task_id}:`, err);
            newResults[task_id] = {
              filename,
              status: 'failed',
              error: err.response?.data?.error || 'Failed to fetch results'
            };
          }
        }
      }

      setResults(newResults);
      setLoading(false);

      // Continue polling if not all tasks are complete
      if (!allCompleted) {
        setTimeout(fetchResults, 2000);
      }
    };

    if (taskIds.length > 0) {
      fetchResults();
    }

    return () => {
      // Cleanup if needed
    };
  }, [taskIds, navigate, location.state]);

  const handleDownloadAll = () => {
    const completedResults = Object.entries(results)
      .filter(([_, result]) => result.status === 'completed')
      .map(([task_id, result]) => ({
        task_id,
        filename: result.filename,
        result: result.result
      }));

    const dataStr = JSON.stringify(completedResults, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `batch-analysis-results.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          Analyzing Files...
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  const completedCount = Object.values(results).filter(r => r.status === 'completed').length;
  const failedCount = Object.values(results).filter(r => r.status === 'failed').length;
  const processingCount = Object.values(results).filter(r => r.status === 'processing').length;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Batch Analysis Results
        </Typography>
        {completedCount > 0 && (
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={handleDownloadAll}
          >
            Download All Results
          </Button>
        )}
      </Box>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item>
          <Chip
            label={`${completedCount} Completed`}
            color="success"
            icon={<CheckCircle />}
          />
        </Grid>
        {processingCount > 0 && (
          <Grid item>
            <Chip
              label={`${processingCount} Processing`}
              color="primary"
            />
          </Grid>
        )}
        {failedCount > 0 && (
          <Grid item>
            <Chip
              label={`${failedCount} Failed`}
              color="error"
              icon={<Error />}
            />
          </Grid>
        )}
      </Grid>

      <List>
        {taskIds.map(({ task_id, filename }) => {
          const result = results[task_id];
          if (!result) return null;

          return (
            <React.Fragment key={task_id}>
              <ListItem>
                <Card sx={{ width: '100%' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6">
                        {filename}
                      </Typography>
                      <Chip
                        label={result.status}
                        color={
                          result.status === 'completed' ? 'success' :
                          result.status === 'failed' ? 'error' : 'primary'
                        }
                        size="small"
                      />
                    </Box>

                    {result.status === 'processing' && (
                      <Box sx={{ width: '100%' }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={progress[task_id] || 0} 
                        />
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          Analysis in progress... {progress[task_id] || 0}%
                        </Typography>
                      </Box>
                    )}

                    {result.status === 'failed' && (
                      <Alert severity="error" sx={{ mt: 1 }}>
                        {result.error}
                      </Alert>
                    )}

                    {result.status === 'completed' && result.result && (
                      <Box>
                        <Grid container spacing={2}>
                          <Grid item xs={12} sm={6}>
                            <Typography variant="subtitle2" color="text.secondary">
                              Risk Level
                            </Typography>
                            <Chip
                              label={result.result.risk_level}
                              color={
                                result.result.risk_level === 'high' ? 'error' :
                                result.result.risk_level === 'medium' ? 'warning' : 'success'
                              }
                              size="small"
                            />
                          </Grid>
                          <Grid item xs={12} sm={6}>
                            <Typography variant="subtitle2" color="text.secondary">
                              Threat Score
                            </Typography>
                            <Typography>
                              {(result.result.threat_score * 100).toFixed(1)}%
                            </Typography>
                          </Grid>
                        </Grid>

                        <Box sx={{ mt: 2 }}>
                          <Button
                            variant="outlined"
                            size="small"
                            onClick={() => navigate(`/analysis/${task_id}`)}
                          >
                            View Full Analysis
                          </Button>
                        </Box>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </ListItem>
              <Divider />
            </React.Fragment>
          );
        })}
      </List>

      <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          onClick={() => navigate('/')}
        >
          Analyze More Files
        </Button>
        {failedCount > 0 && (
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => window.location.reload()}
          >
            Retry Failed
          </Button>
        )}
      </Box>
    </Box>
  );
};

export default BatchAnalysisResult; 