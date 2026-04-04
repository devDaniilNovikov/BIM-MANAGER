import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Button, Card, CardContent, CardActions, Dialog, DialogActions,
  DialogContent, DialogTitle, Grid, IconButton, TextField, Typography,
  CircularProgress, Chip, LinearProgress,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import WarningIcon from '@mui/icons-material/Warning';
import { getProjects, deleteProject, uploadModel } from '../api/projects';
import type { Project } from '../types';

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const load = () => {
    setLoading(true);
    getProjects().then(r => setProjects(r.data)).finally(() => setLoading(false));
  };
  useEffect(load, []);

  const handleUpload = async () => {
    if (!file || !name) return;
    setUploading(true);
    try {
      const res = await uploadModel(file, name, desc || undefined);
      setUploadOpen(false);
      setName(''); setDesc(''); setFile(null);
      navigate(`/project/${res.data.id}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Удалить проект?')) return;
    await deleteProject(id);
    load();
  };

  if (loading) return <Box sx={{ mt: 4 }}><LinearProgress /></Box>;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Проекты</Typography>
        <Button variant="contained" startIcon={<UploadFileIcon />} onClick={() => setUploadOpen(true)}>
          Загрузить модель
        </Button>
      </Box>

      {projects.length === 0 ? (
        <Card sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary" gutterBottom>Нет загруженных проектов</Typography>
          <Button variant="outlined" onClick={() => setUploadOpen(true)}>Загрузить IFC-файл</Button>
        </Card>
      ) : (
        <Grid container spacing={2}>
          {projects.map(p => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={p.id}>
              <Card
                sx={{ cursor: 'pointer', '&:hover': { borderColor: 'primary.main' }, height: '100%', display: 'flex', flexDirection: 'column' }}
                onClick={() => navigate(`/project/${p.id}`)}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" gutterBottom noWrap>{p.name}</Typography>
                  {p.description && <Typography variant="body2" color="text.secondary" gutterBottom>{p.description}</Typography>}
                  <Typography variant="body2" color="text.secondary">{p.file_name} ({formatSize(p.file_size)})</Typography>
                  <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {p.ifc_schema && <Chip label={p.ifc_schema} size="small" />}
                    <Chip label={`${p.element_count ?? 0} элементов`} size="small" color="primary" variant="outlined" />
                    {(p.issue_count ?? 0) > 0 && (
                      <Chip icon={<WarningIcon />} label={`${p.issue_count} замечаний`} size="small" color="warning" variant="outlined" />
                    )}
                  </Box>
                </CardContent>
                <CardActions>
                  <Typography variant="caption" color="text.secondary" sx={{ ml: 1, flexGrow: 1 }}>
                    {new Date(p.created_at).toLocaleDateString('ru-RU')}
                  </Typography>
                  <IconButton size="small" color="error" onClick={(e) => handleDelete(p.id, e)}><DeleteIcon /></IconButton>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Dialog open={uploadOpen} onClose={() => !uploading && setUploadOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Загрузить IFC-модель</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Название проекта" value={name} onChange={e => setName(e.target.value)} margin="normal" required />
          <TextField fullWidth label="Описание" value={desc} onChange={e => setDesc(e.target.value)} margin="normal" multiline rows={2} />
          <input ref={fileRef} type="file" accept=".ifc" hidden onChange={e => setFile(e.target.files?.[0] ?? null)} />
          <Button variant="outlined" fullWidth sx={{ mt: 2 }} onClick={() => fileRef.current?.click()}>
            {file ? file.name : 'Выбрать .ifc файл'}
          </Button>
          {uploading && <LinearProgress sx={{ mt: 2 }} />}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadOpen(false)} disabled={uploading}>Отмена</Button>
          <Button variant="contained" onClick={handleUpload} disabled={!file || !name || uploading}>
            {uploading ? <CircularProgress size={24} /> : 'Загрузить'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
