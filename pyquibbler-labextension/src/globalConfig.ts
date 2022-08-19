
let shouldSaveLoadWithinNotebook = true;

export const getShouldSaveLoadWithinNotebook = () => {
  return shouldSaveLoadWithinNotebook;
}

export const setShouldSaveLoadWithinNotebook = (should: boolean) => {
  shouldSaveLoadWithinNotebook = should;
}
