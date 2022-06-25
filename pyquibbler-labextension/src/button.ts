import styled from "styled-components";


export const Button = styled.button`
 background-color: var(--jp-brand-color1);
 border: none;
 box-shadow: none;
 padding: 6px;
 color: white;
 
 &:hover {
  cursor: pointer;
 }
 &:disabled {
   cursor: not-allowed;
   pointer-events: all !important;
   background-color: var(--jp-layout-color3);
 }
 `