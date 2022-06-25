
let shouldSaveLoadWithinNotebook = true;

let showWithinNotebook = true;

export const getShouldSaveLoadWithinNotebook = () => {
  return shouldSaveLoadWithinNotebook;
}

export const setShouldSaveLoadWithinNotebook = (should: boolean) => {
  shouldSaveLoadWithinNotebook = should;
}

export const getShowWithinNotebook = () => {
  return showWithinNotebook;
}

export const setShowWithinNotebook = (should: boolean) => {
  showWithinNotebook = should;
}
