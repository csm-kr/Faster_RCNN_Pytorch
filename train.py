import os
import time
import torch


def train(epoch, device, vis, train_loader, model, criterion, optimizer, scheduler, opts):

    tic = time.time()
    model.train()

    for idx, data in enumerate(train_loader):

        # set image and GT
        images = data[0]
        boxes = data[1]
        labels = data[2]

        images = images.to(device)
        boxes = [b.to(device) for b in boxes]
        labels = [l.to(device) for l in labels]

        height, width = images.size()[2:]  # height, width
        size = (height, width)
        pred = model(images)   # [cls, reg] - [B, 18, H', W'], [B, 36, H', W']
        loss, cls_loss, reg_loss = criterion(pred, boxes, labels, size)

        # sgd
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        toc = time.time()
        for param_group in optimizer.param_groups:
            lr = param_group['lr']

        # for each steps
        if idx % opts['vis_step'] == 0 or idx == len(train_loader) - 1:
            print('Epoch: [{0}]\t'
                  'Step: [{1}/{2}]\t'
                  'Loss: {loss:.4f}\t'
                  'Cls_loss: {cls_loss:.4f}\t'
                  'Reg_loss: {reg_loss:.4f}\t'
                  'Learning rate: {lr:.7f} s \t'
                  'Time : {time:.4f}\t'
                  .format(epoch, idx, len(train_loader),
                          loss=loss,
                          cls_loss=cls_loss,
                          reg_loss=reg_loss,
                          lr=lr,
                          time=toc - tic))

            if vis is not None:
                # loss plot
                vis.line(X=torch.ones((1, 3)).cpu() * idx + epoch * train_loader.__len__(),  # step
                         Y=torch.Tensor([loss, cls_loss, reg_loss]).unsqueeze(0).cpu(),
                         win='train_loss',
                         update='append',
                         opts=dict(xlabel='step',
                                   ylabel='Loss',
                                   title='training loss',
                                   legend=['Total Loss', 'Cls Loss', 'Reg Loss']))

    if not os.path.exists(opts['save_path']):
        os.mkdir(opts['save_path'])

    checkpoint = {'epoch': epoch,
                  'model_state_dict': model.state_dict(),
                  'optimizer_state_dict': optimizer.state_dict(),
                  'scheduler_state_dict': scheduler.state_dict()}
    torch.save(checkpoint, os.path.join(opts['save_path'], opts['save_file_name'] + '.{}.pth.tar'.format(epoch)))