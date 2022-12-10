import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography,
  Skeleton,
  Tooltip,
} from '@mui/material';
import {
  Error,
  Link as LinkIcon,
  AttachFile,
  Security,
  Refresh,
  Download,
} from '@mui/icons-material';
import axios from 'axios';

const AnalysisResult = () => {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);
  const [progress, setProgress] = useState(0);

  const MAX_RETRIES = 3;
  const POLL_INTERVAL = 2000; // 2 seconds

  const handleError = useCallback((err, context = 'fetching results') => {
    console.error(`Error ${context}:`, err);
    
    let errorMessage = 'An unexpected error occurred';
    
    if (err.response?.status === 404) {
      errorMessage = 'Analysis not found. The task may have expired or never existed.';
    } else if (err.response?.status === 400) {
      errorMessage = 'Invalid task ID. Please check the URL and try again.';
    } else if (err.response?.data?.details) {
      errorMessage = err.response.data.details;
    } else if (err.response?.data?.error) {
      errorMessage = err.response.data.error;
    } else if (err.code === 'NETWORK_ERROR' || err.message.includes('Network Error')) {
      errorMessage = 'Network connection error. Please check your internet connection.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    
    setError(errorMessage);
  }, []);

  const fetchResult = useCallback(async (isRetry = false) => {
    try {
      if (isRetry) {
        setIsRetrying(true);
      }
      
      const response = await axios.get(`/api/analysis/${taskId}`, {
        timeout: 10000, // 10 second timeout
      });
      
      if (!response.data) {
        throw new Error('Empty response from server');
      }
      
      setResult(response.data);
      setError(null);
      setRetryCount(0);
      
      // Update progress if available
      if (response.data.progress !== undefined) {
        setProgress(response.data.progress);
      }

      // Continue polling if still processing
      if (response.data.status === 'processing') {
        setTimeout(() => fetchResult(), POLL_INTERVAL);
      } else {
        setProgress(100);
      }
      
    } catch (err) {
      if (isRetry) {
        handleError(err, 'retrying analysis fetch');
      } else {
        // Auto-retry on certain errors
        if (retryCount < MAX_RETRIES && 
            (err.code === 'NETWORK_ERROR' || err.response?.status >= 500)) {
          setRetryCount(prev => prev + 1);
          setTimeout(() => fetchResult(true), 1000 * Math.pow(2, retryCount)); // Exponential backoff
        } else {
          handleError(err, 'fetching analysis results');
        }
      }
    } finally {
      if (isRetry) {
        setIsRetrying(false);
      }
    }
  }, [taskId, retryCount, handleError]);

  const manualRetry = useCallback(() => {
    setError(null);
    setRetryCount(0);
    fetchResult(true);
  }, [fetchResult]);

  useEffect(() => {
    let isMounted = true;
    let timeoutId;

    if (!taskId) {
      setError('No task ID provided');
      return;
    }

    const fetchWithCleanup = async () => {
      try {
        const response = await axios.get(`/api/analysis/${taskId}`, {
          timeout: 10000,
        });
        
        if (!isMounted) return;
        
        setResult(response.data);
        setError(null);
        
        if (response.data.progress !== undefined) {
          setProgress(response.data.progress);
        }

        // Poll for results if still processing
        if (response.data.status === 'processing') {
          timeoutId = setTimeout(() => {
            if (isMounted) fetchWithCleanup();
          }, POLL_INTERVAL);
        } else {
          setProgress(100);
        }
      } catch (err) {
        if (!isMounted) return;
        
        // Auto-retry logic
        if (retryCount < MAX_RETRIES && 
            (err.code === 'NETWORK_ERROR' || err.response?.status >= 500)) {
          setRetryCount(prev => prev + 1);
          timeoutId = setTimeout(() => {
            if (isMounted) fetchWithCleanup();
          }, 1000 * Math.pow(2, retryCount));
        } else {
          handleError(err);
        }
      }
    };

    fetchWithCleanup();

    // Cleanup function
    return () => {
      isMounted = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [taskId, retryCount, handleError]);

  const getRiskColor = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'success';
      default:
        return 'info';
    }
  };

  const LoadingSkeleton = () => (
    <Box>
      <Skeleton variant="text" width="60%" height={60} />
      <Skeleton variant="rectangular" width="100%" height={200} sx={{ mt: 2 }} />
      <Grid container spacing={2} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Skeleton variant="rectangular" height={300} />
        </Grid>
        <Grid item xs={12} md={6}>
          <Skeleton variant="rectangular" height={300} />
        </Grid>
      </Grid>
    </Box>
  );

  if (error) {
    return (
      <Box sx={{ mt: 4 }}>
        <Alert 
          severity="error" 
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={manualRetry}
              disabled={isRetrying}
              startIcon={isRetrying ? <CircularProgress size={16} /> : <Refresh />}
            >
              {isRetrying ? 'Retrying...' : 'Retry'}
            </Button>
          }
        >
          <Typography variant="subtitle2" gutterBottom>
            Analysis Error
          </Typography>
          {error}
          {retryCount > 0 && (
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Retry attempt: {retryCount}/{MAX_RETRIES}
            </Typography>
          )}
        </Alert>
        <Box sx={{ mt: 2 }}>
          <Button
            variant="contained"
            onClick={() => navigate('/')}
          >
            Start New Analysis
          </Button>
        </Box>
      </Box>
    );
  }

  if (!result) {
    return (
      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          Loading Analysis Results...
        </Typography>
        <LinearProgress sx={{ mb: 2 }} />
        <LoadingSkeleton />
      </Box>
    );
  }

  if (result.status === 'processing') {
    return (
      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          Analyzing Email...
        </Typography>
        <LinearProgress 
          variant="determinate" 
          value={progress} 
          sx={{ mb: 2 }}
        />
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {result.message || 'Analysis in progress...'}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Progress: {progress}% • Task ID: {taskId}
        </Typography>
        <LoadingSkeleton />
      </Box>
    );
  }

  if (result.status === 'failed' || !result.result) {
    return (
      <Box sx={{ mt: 4 }}>
        <Alert severity="error">
          <Typography variant="subtitle2" gutterBottom>
            Analysis Failed
          </Typography>
          {result.error || 'Unknown error occurred during analysis'}
        </Alert>
        <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            onClick={() => navigate('/')}
          >
            Try Again
          </Button>
          <Button
            variant="outlined"
            onClick={manualRetry}
            disabled={isRetrying}
            startIcon={isRetrying ? <CircularProgress size={16} /> : <Refresh />}
          >
            {isRetrying ? 'Retrying...' : 'Retry Analysis'}
          </Button>
        </Box>
      </Box>
    );
  }

  const { result: analysis } = result;

  if (!analysis) {
    return (
      <Box sx={{ mt: 4 }}>
        <Alert severity="warning">
          Analysis completed but no results were returned. This may indicate a processing error.
        </Alert>
        <Button
          variant="contained"
          onClick={() => navigate('/')}
          sx={{ mt: 2 }}
        >
          Start New Analysis
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Analysis Results
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Download results as JSON">
            <Button
              variant="outlined"
              size="small"
              startIcon={<Download />}
              onClick={() => {
                const dataStr = JSON.stringify(analysis, null, 2);
                const dataBlob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(dataBlob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `phishing-analysis-${taskId}.json`;
                link.click();
                URL.revokeObjectURL(url);
              }}
            >
              Export
            </Button>
          </Tooltip>
        </Box>
      </Box>

      {/* Email Info */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Email Information
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" color="text.secondary">
                Subject
              </Typography>
              <Typography variant="body2">
                {analysis.subject || 'No Subject'}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" color="text.secondary">
                Sender
              </Typography>
              <Typography variant="body2">
                {analysis.sender || 'Unknown'}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" color="text.secondary">
                Timestamp
              </Typography>
              <Typography variant="body2">
                {analysis.timestamp || 'Unknown'}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Overall Score */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Grid container alignItems="center" spacing={2}>
            <Grid item xs={12} md={8}>
              <Typography variant="h5" gutterBottom>
                Threat Score: {((analysis.threat_score || 0) * 100).toFixed(1)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(analysis.threat_score || 0) * 100}
                color={getRiskColor(analysis.risk_level)}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Grid>
            <Grid item xs={12} md={4} sx={{ textAlign: { md: 'right' } }}>
              <Chip
                label={`${(analysis.risk_level || 'unknown').toUpperCase()} RISK`}
                color={getRiskColor(analysis.risk_level)}
                size="large"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Recommendations */}
      {analysis.recommendations && analysis.recommendations.length > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Security Recommendations
            </Typography>
            <List>
              {analysis.recommendations.map((recommendation, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Security color="primary" />
                  </ListItemIcon>
                  <ListItemText primary={recommendation} />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      <Grid container spacing={4}>
        {/* Header Analysis */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Header Analysis
              </Typography>
              
              {analysis.header_analysis?.risk_indicators?.length > 0 ? (
                <List>
                  {analysis.header_analysis.risk_indicators.map((indicator, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <Error color="error" />
                      </ListItemIcon>
                      <ListItemText primary={indicator} />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  No header-based risk indicators detected
                </Typography>
              )}
              
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" gutterBottom>
                Authentication Results
              </Typography>
              
              {analysis.header_analysis?.authentication_results && 
               Object.keys(analysis.header_analysis.authentication_results).length > 0 ? (
                <Box>
                  {Object.entries(analysis.header_analysis.authentication_results).map(
                    ([key, value]) => (
                      <Chip
                        key={key}
                        label={`${key.toUpperCase()}: ${value}`}
                        color={value === 'passed' ? 'success' : 'error'}
                        sx={{ mr: 1, mb: 1 }}
                      />
                    )
                  )}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No authentication data available
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Content Analysis */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Content Analysis
              </Typography>
              
              <Typography variant="subtitle2" gutterBottom>
                Suspicious Keywords
              </Typography>
              <Box sx={{ mb: 2, minHeight: 40 }}>
                {analysis.content_analysis?.suspicious_keywords?.length > 0 ? (
                  analysis.content_analysis.suspicious_keywords.map((keyword, index) => (
                    <Chip
                      key={index}
                      label={keyword}
                      color="warning"
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No suspicious keywords detected
                  </Typography>
                )}
              </Box>
              
              <Typography variant="subtitle2" gutterBottom>
                Urgency Indicators
              </Typography>
              <Box sx={{ minHeight: 40 }}>
                {analysis.content_analysis?.urgency_indicators?.length > 0 ? (
                  analysis.content_analysis.urgency_indicators.map((indicator, index) => (
                    <Chip
                      key={index}
                      label={indicator}
                      color="error"
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No urgency indicators detected
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Link Analysis */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Link Analysis
              </Typography>
              
              {(analysis.link_analysis?.suspicious_links?.length > 0 || 
                analysis.link_analysis?.malicious_domains?.length > 0) ? (
                <List>
                  {analysis.link_analysis.suspicious_links?.map((link, index) => (
                    <ListItem key={`link-${index}`}>
                      <ListItemIcon>
                        <LinkIcon color="warning" />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              wordBreak: 'break-all',
                              maxWidth: '100%'
                            }}
                          >
                            {link}
                          </Typography>
                        }
                        secondary="Suspicious URL detected"
                      />
                    </ListItem>
                  )) || []}
                  {analysis.link_analysis.malicious_domains?.map((domain, index) => (
                    <ListItem key={`domain-${index}`}>
                      <ListItemIcon>
                        <Error color="error" />
                      </ListItemIcon>
                      <ListItemText
                        primary={domain}
                        secondary="Known malicious domain"
                      />
                    </ListItem>
                  )) || []}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No suspicious links or malicious domains detected
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Attachment Analysis */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Attachment Analysis
              </Typography>
              
              {analysis.attachment_analysis?.suspicious_attachments?.length > 0 ? (
                <List>
                  {analysis.attachment_analysis.suspicious_attachments.map(
                    (attachment, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <AttachFile color="error" />
                        </ListItemIcon>
                        <ListItemText
                          primary={attachment}
                          secondary="Suspicious attachment detected"
                        />
                      </ListItem>
                    )
                  )}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  No suspicious attachments detected
                </Typography>
              )}
              
              <Typography variant="subtitle2" gutterBottom>
                File Types Found
              </Typography>
              <Box sx={{ minHeight: 40 }}>
                {analysis.attachment_analysis?.file_types?.length > 0 ? (
                  analysis.attachment_analysis.file_types.map((type, index) => (
                    <Chip
                      key={index}
                      label={type.toUpperCase()}
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No attachments found
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Action Buttons */}
      <Box sx={{ mt: 4, mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Button 
          variant="contained" 
          onClick={() => navigate('/')}
          size="large"
        >
          Analyze Another Email
        </Button>
        <Button 
          variant="outlined" 
          onClick={() => window.print()}
          size="large"
        >
          Print Results
        </Button>
      </Box>
      
      {/* Analysis metadata */}
      <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
        <Typography variant="caption" color="text.secondary">
          Analysis ID: {taskId} • Completed at: {new Date().toLocaleString()}
        </Typography>
      </Box>
    </Box>
  );
};

export default AnalysisResult; 