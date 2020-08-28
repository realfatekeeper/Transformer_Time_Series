#!/usr/bin/env python
# coding: utf-8


import torch
import matplotlib.pyplot as plt
import numpy as np
from torch.utils.data import Dataset


class time_series_paper(Dataset):
    """synthetic time series dataset from section 5.1"""
    
    def __init__(self,t0=96,N=4500,transform=None):
        """
        Args:
            t0: previous t0 data points to predict from
            N: number of data points
            transform: any transformations to be applied to time series
        """
        self.t0 = t0
        self.N = N
        self.transform = None
        
        # time points
        self.x = torch.cat(N*[torch.arange(0,t0+24).type(torch.float).unsqueeze(0)])

        # sinuisoidal signal
        A1,A2,A3 = 60 * torch.rand(3,N)
        A4 = torch.max(A1,A2)        
        self.fx = torch.cat([A1.unsqueeze(1)*torch.sin(np.pi*self.x[0,0:12]/6)+72 ,
                        A2.unsqueeze(1)*torch.sin(np.pi*self.x[0,12:24]/6)+72 ,
                        A3.unsqueeze(1)*torch.sin(np.pi*self.x[0,24:t0]/6)+72,
                        A4.unsqueeze(1)*torch.sin(np.pi*self.x[0,t0:t0+24]/12)+72],1)
        
        # add noise
        self.fx = self.fx + torch.randn(self.fx.shape)
        
        self.masks = self._generate_square_subsequent_mask(24+1)
                
        
        # print out shapes to confirm desired output
        print("x: {}*{}".format(*list(self.x.shape)),
              "fx: {}*{}".format(*list(self.fx.shape)))        
        
    def __len__(self):
        return len(self.fx)
    
    def __getitem__(self,idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()
            
        #sample = {"x":self.x[idx,0:self.t0],
        #          "x_next":self.x[idx,self.t0:self.t0+24],
        #          "fx": self.fx[idx,0:self.t0],
        #          "fx_next":self.fx[idx,self.t0:self.t0+24],
        #          "attention_masks":self.masks}
        
        sample = (self.x[idx,0:self.t0-1],
                  self.x[idx,self.t0-1:self.t0+24],
                  self.fx[idx,0:self.t0-1],
                  self.fx[idx,self.t0-1:self.t0+24],
                  self.masks)
        
        if self.transform:
            sample=self.transform(sample)
            
        return sample
    
    def _generate_square_subsequent_mask(self,sz):
        mask = (torch.triu(torch.ones(sz, sz)) == 1).transpose(0, 1)
        mask = mask.float().masked_fill(mask == 0, float('-inf')).masked_fill(mask == 1, float(0.0))
        return mask

class time_series_missing_paper(Dataset):
    """synthetic time series dataset from section 5.1"""
    
    def __init__(self,t0=96,N=4500,missing_chunk=50,transform=None):
        """
        Args:
            t0: previous t0 data points to predict from
            N: number of data points
            transform: any transformations to be applied to time series
        """
        self.t0 = t0
        self.N = N
        self.transform = None
        
        # time points
        self.x = torch.cat(N*[torch.arange(0,t0+24).type(torch.float).unsqueeze(0)])

        # sinuisoidal signal
        A1,A2,A3 = 60 * torch.rand(3,N)
        A4 = torch.max(A1,A2)        
        self.fx = torch.cat([A1.unsqueeze(1)*torch.sin(np.pi*self.x[0,0:12]/6)+72 ,
                        A2.unsqueeze(1)*torch.sin(np.pi*self.x[0,12:24]/6)+72 ,
                        A3.unsqueeze(1)*torch.sin(np.pi*self.x[0,24:t0]/6)+72,
                        A4.unsqueeze(1)*torch.sin(np.pi*self.x[0,t0:t0+24]/12)+72],1)
        
        # add noise
        self.fx = self.fx + torch.randn(self.fx.shape)
        

        src_mask = torch.zeros(t0-1,t0-1)
        
        self.fx_missing = torch.zeros((N,t0+24-missing_chunk)) 
        self.x_missing = torch.zeros((N,t0+24-missing_chunk)) 
        
        self.x_prior = torch.zeros((N,t0-1-missing_chunk))
        self.x_post = torch.zeros((N,1+24))
        self.fx_prior = torch.zeros((N,t0-1-missing_chunk))
        self.fx_post = torch.zeros((N,1+24))
        
        for j in range(0,self.fx.shape[0]):
            missing_idx = torch.randint(24,t0-1-missing_chunk,(1,)).item()
            desired_idx = torch.LongTensor([i for i in np.arange(0,t0+24) if i not in np.arange(missing_idx,missing_idx+missing_chunk)])
            
            
            self.fx_missing[j,:] = self.fx[j,desired_idx]
            self.x_missing[j,:] = self.x[j,desired_idx]
                        
            idx1 = desired_idx[desired_idx < (t0-1)].squeeze()
            idx2 = desired_idx[desired_idx >= (t0-1)].squeeze()

            self.x_prior[j,:] = self.x[j,idx1]
            self.x_post[j,:] = self.x[j,idx2]
            self.fx_prior[j,:] = self.fx[j,idx1]
            self.fx_post[j,:] = self.fx[j,idx2]
        
            
        self.masks = self._generate_square_subsequent_mask(24+1)
        
                
        
        # print out shapes to confirm desired output
        print("x: {}*{}".format(*list(self.x.shape)),
              "fx: {}*{}".format(*list(self.fx.shape)))        
        
    def __len__(self):
        return len(self.fx)
    
    def __getitem__(self,idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()
            
        #sample = {"x":self.x[idx,0:self.t0],
        #          "x_next":self.x[idx,self.t0:self.t0+24],
        #          "fx": self.fx[idx,0:self.t0],
        #          "fx_next":self.fx[idx,self.t0:self.t0+24],
        #          "attention_masks":self.masks}
        
        sample = (self.x_prior[idx],
                  self.x_post[idx],
                  self.fx_prior[idx],
                  self.fx_post[idx],
                  self.masks)
        
        if self.transform:
            sample=self.transform(sample)
            
        return sample
    
    def _generate_square_subsequent_mask(self,sz):
        mask = (torch.triu(torch.ones(sz, sz)) == 1).transpose(0, 1)
        mask = mask.float().masked_fill(mask == 0, float('-inf')).masked_fill(mask == 1, float(0.0))
        return mask
    
class time_series_decoder_paper(Dataset):
    """synthetic time series dataset from section 5.1"""
    
    def __init__(self,t0=96,N=4500,transform=None):
        """
        Args:
            t0: previous t0 data points to predict from
            N: number of data points
            transform: any transformations to be applied to time series
        """
        self.t0 = t0
        self.N = N
        self.transform = None
        
        # time points
        self.x = torch.cat(N*[torch.arange(0,t0+24).type(torch.float).unsqueeze(0)])

        # sinuisoidal signal
        A1,A2,A3 = 60 * torch.rand(3,N)
        A4 = torch.max(A1,A2)        
        self.fx = torch.cat([A1.unsqueeze(1)*torch.sin(np.pi*self.x[0,0:12]/6)+72 ,
                        A2.unsqueeze(1)*torch.sin(np.pi*self.x[0,12:24]/6)+72 ,
                        A3.unsqueeze(1)*torch.sin(np.pi*self.x[0,24:t0]/6)+72,
                        A4.unsqueeze(1)*torch.sin(np.pi*self.x[0,t0:t0+24]/12)+72],1)
        
        # add noise
        self.fx = self.fx + torch.randn(self.fx.shape)
        
        self.masks = self._generate_square_subsequent_mask(t0)
                
        
        # print out shapes to confirm desired output
        print("x: {}*{}".format(*list(self.x.shape)),
              "fx: {}*{}".format(*list(self.fx.shape)))        
        
    def __len__(self):
        return len(self.fx)
    
    def __getitem__(self,idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()
            
        
        sample = (self.x[idx,:],
                  self.fx[idx,:],
                  self.masks)
        
        if self.transform:
            sample=self.transform(sample)
            
        return sample
    
    def _generate_square_subsequent_mask(self,t0):
        mask = torch.zeros(t0+24,t0+24)
        for i in range(0,t0):
            mask[i,t0:] = 1 
        for i in range(t0,t0+24):
            mask[i,i+1:] = 1
        mask = mask.float().masked_fill(mask == 1, float('-inf'))#.masked_fill(mask == 1, float(0.0))
        return mask