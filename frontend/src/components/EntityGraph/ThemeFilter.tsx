import { Group, Chip } from '@mantine/core';

interface Props {
  selectedThemes: string[];
  onChange: (themes: string[]) => void;
}

const THEME_OPTIONS = [
  { value: 'sanctions', label: 'Sanctions', color: 'red' },
  { value: 'trade', label: 'Trade', color: 'blue' },
  { value: 'political', label: 'Political', color: 'violet' },
  { value: 'energy', label: 'Energy', color: 'orange' },
  { value: 'adversarial', label: 'Adversarial', color: 'grape' },
];

export const ThemeFilter = ({ selectedThemes, onChange }: Props) => {
  return (
    <Chip.Group multiple value={selectedThemes} onChange={onChange}>
      <Group gap="xs">
        {THEME_OPTIONS.map(theme => (
          <Chip key={theme.value} value={theme.value} color={theme.color}>
            {theme.label}
          </Chip>
        ))}
      </Group>
    </Chip.Group>
  );
};
