import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Tab,
  Tabs,
  TextField,
  Typography,
  Alert,
} from '@mui/material';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Dashboard = () => {
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [emailContent, setEmailContent] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'message/rfc822': ['.eml'],
    },
    maxSize: 16 * 1024 * 1024, // 16MB
    multiple: false,
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        await handleFileUpload(acceptedFiles[0]);
      }
    },
  });

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setError(null);
  };

  const handleFileUpload = async (file) => {
    setError(null);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('/api/analyze/file', formData);
      navigate(`/analysis/${response.data.task_id}`);
    } catch (err) {
      setError(
        err.response?.data?.error || 'An error occurred while uploading the file'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleContentSubmit = async () => {
    if (!emailContent.trim()) {
      setError('Please enter email content');
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      const response = await axios.post('/api/analyze/content', {
        content: emailContent,
      });
      navigate(`/analysis/${response.data.task_id}`);
    } catch (err) {
      setError(
        err.response?.data?.error || 'An error occurred while analyzing the content'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Email Phishing Analysis
      </Typography>
      
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload an email file (.eml) or paste email content to analyze it for potential phishing threats.
      </Typography>

      <Card sx={{ mt: 4 }}>
        <CardContent>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange}>
              <Tab label="Upload File" />
              <Tab label="Paste Content" />
            </Tabs>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}

          <TabPanel value={tabValue} index={0}>
            <Box
              {...getRootProps()}
              sx={{
                border: '2px dashed',
                borderColor: isDragActive ? 'primary.main' : 'grey.300',
                borderRadius: 1,
                p: 3,
                textAlign: 'center',
                cursor: 'pointer',
                '&:hover': {
                  borderColor: 'primary.main',
                },
              }}
            >
              <input {...getInputProps()} />
              <Typography>
                {isDragActive
                  ? 'Drop the file here'
                  : 'Drag and drop an .eml file here, or click to select file'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Maximum file size: 16MB
              </Typography>
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  multiline
                  rows={10}
                  fullWidth
                  placeholder="Paste email content here..."
                  value={emailContent}
                  onChange={(e) => setEmailContent(e.target.value)}
                />
              </Grid>
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  onClick={handleContentSubmit}
                  disabled={isLoading || !emailContent.trim()}
                >
                  {isLoading ? 'Analyzing...' : 'Analyze Content'}
                </Button>
              </Grid>
            </Grid>
          </TabPanel>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Dashboard; 