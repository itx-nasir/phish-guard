import React, { useEffect, useState } from 'react';
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
} from '@mui/material';
import {
  CheckCircle,
  Error,
  Warning,
  Link as LinkIcon,
  AttachFile,
  Security,
} from '@mui/icons-material';
import axios from 'axios';

interface AnalysisResult {
  status: string;
  result?: {
    threat_score: number;
    risk_level: string;
    header_analysis: {
      suspicious_patterns: string[];
      authentication_results: Record<string, string>;
      risk_indicators: string[];
    };
    content_analysis: {
      suspicious_keywords: string[];
      urgency_indicators: string[];
    };
    link_analysis: {
      suspicious_links: string[];
      redirects: string[];
      malicious_domains: string[];
    };
    attachment_analysis: {
      suspicious_attachments: string[];
      file_types: string[];
    };
    recommendations: string[];
  };
  error?: string;
}

const AnalysisResult: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResult = async () => {
      try {
        const response = await axios.get(`/api/analysis/${taskId}`);
        setResult(response.data);

        // Poll for results if still processing
        if (response.data.status === 'processing') {
          setTimeout(() => fetchResult(), 2000);
        }
      } catch (err: any) {
        setError(err.response?.data?.error || 'Failed to fetch analysis results');
      }
    };

    fetchResult();
  }, [taskId]);

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
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

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!result) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (result.status === 'processing') {
    return (
      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          Analyzing Email...
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  if (result.status === 'failed' || !result.result) {
    return (
      <Box sx={{ mt: 4 }}>
        <Alert severity="error">
          Analysis failed: {result.error || 'Unknown error occurred'}
        </Alert>
        <Button
          variant="contained"
          onClick={() => navigate('/')}
          sx={{ mt: 2 }}
        >
          Try Again
        </Button>
      </Box>
    );
  }

  const { result: analysis } = result;

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Analysis Results
      </Typography>

      {/* Overall Score */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Grid container alignItems="center" spacing={2}>
            <Grid item>
              <Typography variant="h5">
                Threat Score: {(analysis.threat_score * 100).toFixed(1)}%
              </Typography>
            </Grid>
            <Grid item>
              <Chip
                label={analysis.risk_level.toUpperCase()}
                color={getRiskColor(analysis.risk_level) as any}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recommendations
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

      <Grid container spacing={4}>
        {/* Header Analysis */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Header Analysis
              </Typography>
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
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" gutterBottom>
                Authentication Results
              </Typography>
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
            </CardContent>
          </Card>
        </Grid>

        {/* Content Analysis */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Content Analysis
              </Typography>
              <Typography variant="subtitle2" gutterBottom>
                Suspicious Keywords
              </Typography>
              <Box sx={{ mb: 2 }}>
                {analysis.content_analysis.suspicious_keywords.map((keyword, index) => (
                  <Chip
                    key={index}
                    label={keyword}
                    color="warning"
                    sx={{ mr: 1, mb: 1 }}
                  />
                ))}
              </Box>
              <Typography variant="subtitle2" gutterBottom>
                Urgency Indicators
              </Typography>
              <Box>
                {analysis.content_analysis.urgency_indicators.map((indicator, index) => (
                  <Chip
                    key={index}
                    label={indicator}
                    color="error"
                    sx={{ mr: 1, mb: 1 }}
                  />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Link Analysis */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Link Analysis
              </Typography>
              <List>
                {analysis.link_analysis.suspicious_links.map((link, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <LinkIcon color="warning" />
                    </ListItemIcon>
                    <ListItemText
                      primary={link}
                      secondary="Suspicious URL detected"
                    />
                  </ListItem>
                ))}
                {analysis.link_analysis.malicious_domains.map((domain, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <Error color="error" />
                    </ListItemIcon>
                    <ListItemText
                      primary={domain}
                      secondary="Known malicious domain"
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Attachment Analysis */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Attachment Analysis
              </Typography>
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
              <Typography variant="subtitle2" gutterBottom>
                File Types
              </Typography>
              <Box>
                {analysis.attachment_analysis.file_types.map((type, index) => (
                  <Chip
                    key={index}
                    label={type.toUpperCase()}
                    sx={{ mr: 1, mb: 1 }}
                  />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 4, mb: 2 }}>
        <Button variant="contained" onClick={() => navigate('/')}>
          Analyze Another Email
        </Button>
      </Box>
    </Box>
  );
};

export default AnalysisResult;