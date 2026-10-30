"use client";
/* eslint-disable @next/next/no-img-element -- previews can use Qloo-hosted artwork. */
import {useEffect,useId,useRef} from "react";
import {createRoot} from "react-dom/client";
import {Trash2} from "lucide-react";

type ConfirmDialogProps={open:boolean;title:string;description:string;confirmLabel:string;cancelLabel:string;tone?:"neutral"|"destructive";eyebrow?:string;preview?:{name:string;type:string;image?:string};onConfirm:()=>void;onCancel:()=>void};
export function ConfirmDialog({open,title,description,confirmLabel,cancelLabel,tone="neutral",eyebrow="Please confirm",preview,onConfirm,onCancel}:ConfirmDialogProps){
 const dialogRef=useRef<HTMLElement>(null),cancelRef=useRef<HTMLButtonElement>(null),openerRef=useRef<HTMLElement|null>(null),cancelHandler=useRef(onCancel),titleId=useId(),descriptionId=useId();
 useEffect(()=>{cancelHandler.current=onCancel},[onCancel]);
 useEffect(()=>{if(!open)return;openerRef.current=document.activeElement as HTMLElement;const frame=requestAnimationFrame(()=>cancelRef.current?.focus()),escape=(event:KeyboardEvent)=>{if(event.key!=="Escape")return;event.preventDefault();event.stopImmediatePropagation();cancelHandler.current()};window.addEventListener("keydown",escape,true);return()=>{cancelAnimationFrame(frame);window.removeEventListener("keydown",escape,true);openerRef.current?.focus()}},[open]);
 if(!open)return null;
 return <div className="confirm-backdrop" onPointerDown={event=>{if(event.target===event.currentTarget)onCancel()}}><section ref={dialogRef} className={`confirm-dialog ${tone}`} role="alertdialog" aria-modal="true" aria-labelledby={titleId} aria-describedby={descriptionId} onKeyDown={event=>{if(event.key==="Escape"){event.preventDefault();event.stopPropagation();onCancel();return}if(event.key!=="Tab")return;const items=Array.from(dialogRef.current?.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],input:not(:disabled)')??[]);if(!items.length)return;const first=items[0],last=items.at(-1)!;if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}}}>
  <div className="confirm-mark"><Trash2 aria-hidden="true"/></div><div className="confirm-copy"><span>{eyebrow}</span><h2 id={titleId}>{title}</h2><p id={descriptionId}>{description}</p></div>
  {preview&&<div className="confirm-preview">{preview.image?<img src={preview.image} alt=""/>:<i>{preview.name.slice(0,1)}</i>}<span><small>{preview.type.replaceAll("_"," ")}</small><b>{preview.name}</b></span></div>}
  <footer><button ref={cancelRef} type="button" className="confirm-safe" onClick={onCancel}>{cancelLabel}</button><button type="button" className="confirm-danger" onClick={onConfirm}>{confirmLabel}</button></footer>
 </section></div>
}

export function confirmWithDialog(options:Omit<ConfirmDialogProps,"open"|"onConfirm"|"onCancel">){
 return new Promise<boolean>(resolve=>{
  const mount=document.createElement("div"),root=createRoot(mount);document.body.appendChild(mount);
  const finish=(answer:boolean)=>{root.unmount();mount.remove();resolve(answer)};
  root.render(<ConfirmDialog {...options} open onConfirm={()=>finish(true)} onCancel={()=>finish(false)}/>);
 });
}
