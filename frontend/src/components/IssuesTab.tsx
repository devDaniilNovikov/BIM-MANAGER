import { useEffect, useState, useCallback } from 'react';
import {
  Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle,
  MenuItem, Pagination, Paper, Stack, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, TextField, Typography, LinearProgress,
  IconButton,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import { getIssues, createIssue, updateIssue, deleteIssue } from '../api/issues';
import type { Issue, IssueCreate } from '../types';

interface Props { projectId: string; }

const severityColor = (s: string) => s === 'error' ? 'error' : s === 'warning' ? 'warning' : 'info';
const statusColor = (s: string) => s === 'resolved' ? 'success' : s === 'ignored' ? 'default' : s === 'in_progress' ? 'primary' : 'warning';

export default function IssuesTab({ projectId }: Props) {
  const [items, setItems] = useState<Issue[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [newIssue, setNewIssue] = useState<IssueCreate>({ category: '', message: '', severity: 'warning' });
  const pageSize = 50;

  const load = useCallback(() => {
    setLoading(true);
    getIssues(projectId, {
      status: filterStatus || undefined,
      severity: filterSeverity || undefined,
      page,
      page_size: pageSize,
    }).then(r => { setItems(r.data.items); setTotal(r.data.total); })
      .finally(() => setLoading(false));
  }, [projectId, filterStatus, filterSeverity, page]);

  useEffect(load, [load]);

  const handleStatusChange = async (issue: Issue, status: string) => {
    await updateIssue(projectId, issue.id, { status });
    load();
  };

  const handleDelete = async (id: string) => {
    await deleteIssue(projectId, id);
    load();
  };

  const handleCreate = async () => {
    if (!newIssue.category || !newIssue.message) return;
    await createIssue(projectId, newIssue);
    setCreateOpen(false);
    setNewIssue({ category: '', message: '', severity: 'warning' });
    load();
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Замечания</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
          Создать замечание
        </Button>
      </Box>

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
        <TextField select size="small" label="Статус" value={filterStatus} onChange={e => { setFilterStatus(e.target.value); setPage(1); }} sx={{ minWidth: 150 }}>
          <MenuItem value="">Все</MenuItem>
          <MenuItem value="open">Открытые</MenuItem>
          <MenuItem value="in_progress">В работе</MenuItem>
          <MenuItem value="resolved">Решённые</MenuItem>
          <MenuItem value="ignored">Игнорированные</MenuItem>
        </TextField>
        <TextField select size="small" label="Критичность" value={filterSeverity} onChange={e => { setFilterSeverity(e.target.value); setPage(1); }} sx={{ minWidth: 150 }}>
          <MenuItem value="">Все</MenuItem>
          <MenuItem value="error">Ошибка</MenuItem>
          <MenuItem value="warning">Предупреждение</MenuItem>
          <MenuItem value="info">Информация</MenuItem>
        </TextField>
        <Typography variant="body2" color="text.secondary" sx={{ alignSelf: 'center' }}>
          Всего: {total}
        </Typography>
      </Stack>

      {loading && <LinearProgress sx={{ mb: 1 }} />}

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Критичность</TableCell>
              <TableCell>Категория</TableCell>
              <TableCell>Сообщение</TableCell>
              <TableCell>Рекомендация</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map(iss => (
              <TableRow key={iss.id}>
                <TableCell><Chip label={iss.severity} size="small" color={severityColor(iss.severity)} /></TableCell>
                <TableCell><Typography variant="body2">{iss.category}</Typography></TableCell>
                <TableCell sx={{ maxWidth: 300 }}><Typography variant="body2" noWrap>{iss.message}</Typography></TableCell>
                <TableCell sx={{ maxWidth: 250 }}>
                  <Typography variant="body2" color="primary" noWrap>{iss.recommendation || '—'}</Typography>
                </TableCell>
                <TableCell>
                  <TextField
                    select size="small" value={iss.status}
                    onChange={e => handleStatusChange(iss, e.target.value)}
                    sx={{ minWidth: 130 }}
                  >
                    <MenuItem value="open">Открыто</MenuItem>
                    <MenuItem value="in_progress">В работе</MenuItem>
                    <MenuItem value="resolved">Решено</MenuItem>
                    <MenuItem value="ignored">Игнор</MenuItem>
                  </TextField>
                </TableCell>
                <TableCell>
                  <IconButton size="small" color="error" onClick={() => handleDelete(iss.id)}><DeleteIcon fontSize="small" /></IconButton>
                </TableCell>
              </TableRow>
            ))}
            {items.length === 0 && !loading && (
              <TableRow><TableCell colSpan={6} align="center">Нет замечаний</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {total > pageSize && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Pagination count={Math.ceil(total / pageSize)} page={page} onChange={(_, v) => setPage(v)} />
        </Box>
      )}

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Новое замечание</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth label="Категория" margin="normal" required
            value={newIssue.category} onChange={e => setNewIssue({ ...newIssue, category: e.target.value })}
            placeholder="missing_name, missing_storey, custom..."
          />
          <TextField
            fullWidth label="Заголовок" margin="normal"
            value={newIssue.title || ''} onChange={e => setNewIssue({ ...newIssue, title: e.target.value })}
          />
          <TextField
            fullWidth label="Сообщение" margin="normal" required multiline rows={3}
            value={newIssue.message} onChange={e => setNewIssue({ ...newIssue, message: e.target.value })}
          />
          <TextField
            select fullWidth label="Критичность" margin="normal"
            value={newIssue.severity} onChange={e => setNewIssue({ ...newIssue, severity: e.target.value })}
          >
            <MenuItem value="error">Ошибка</MenuItem>
            <MenuItem value="warning">Предупреждение</MenuItem>
            <MenuItem value="info">Информация</MenuItem>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Отмена</Button>
          <Button variant="contained" onClick={handleCreate}>Создать</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
