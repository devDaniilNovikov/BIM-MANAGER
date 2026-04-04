import { useState } from 'react';
import {
  Box, Typography, Accordion, AccordionSummary, AccordionDetails,
  List, ListItem, ListItemIcon, ListItemText, Chip,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ApartmentIcon from '@mui/icons-material/Apartment';
import LayersIcon from '@mui/icons-material/Layers';
import MeetingRoomIcon from '@mui/icons-material/MeetingRoom';
import type { Building } from '../types';

interface Props {
  projectId: string;
  buildings: Building[];
}

export default function StructureTab({ buildings }: Props) {
  if (buildings.length === 0) {
    return <Typography color="text.secondary">Пространственная структура не найдена</Typography>;
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Структура проекта</Typography>
      {buildings.map(b => (
        <Accordion key={b.id} defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <ApartmentIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="subtitle1" fontWeight={600}>
              {b.name || 'Здание'} <Chip label={`${b.storeys.length} этажей`} size="small" sx={{ ml: 1 }} />
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            {b.storeys
              .sort((a, c) => (c.elevation ?? 0) - (a.elevation ?? 0))
              .map(s => (
                <Accordion key={s.id} variant="outlined" sx={{ mb: 1 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <LayersIcon sx={{ mr: 1, color: 'secondary.main' }} />
                    <Typography>
                      {s.name || 'Этаж'}
                      {s.elevation != null && <Chip label={`${s.elevation.toFixed(1)} м`} size="small" sx={{ ml: 1 }} />}
                      <Chip label={`${s.spaces.length} помещений`} size="small" sx={{ ml: 1 }} variant="outlined" />
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    {s.spaces.length === 0 ? (
                      <Typography variant="body2" color="text.secondary">Нет помещений</Typography>
                    ) : (
                      <List dense>
                        {s.spaces.map(sp => (
                          <ListItem key={sp.id}>
                            <ListItemIcon><MeetingRoomIcon fontSize="small" /></ListItemIcon>
                            <ListItemText
                              primary={sp.name || sp.long_name || 'Помещение'}
                              secondary={[
                                sp.area != null ? `Площадь: ${sp.area.toFixed(2)} м²` : null,
                                sp.volume != null ? `Объём: ${sp.volume.toFixed(2)} м³` : null,
                              ].filter(Boolean).join(' | ')}
                            />
                          </ListItem>
                        ))}
                      </List>
                    )}
                  </AccordionDetails>
                </Accordion>
              ))}
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}
