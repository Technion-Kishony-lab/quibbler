import numpy as np
from matplotlib import pyplot as plt, widgets
from mpl_toolkits.axes_grid1 import ImageGrid

from pyquibbler import iquib, q, override_all, CacheBehavior

override_all()


def create_roi(roi, axes):
    widgets.RectangleSelector(axes, extents=roi)


def cut_image(roi):
    im = image[roi[2]:roi[3], roi[0]:roi[1]]
    return im


def image_distance(img1, img2):
    rgb1 = np.mean(img1, axis=(1, 2))
    rgb2 = np.mean(img2, axis=(1, 2))
    return 1 - np.corrcoef(rgb1, rgb2)


file_name = iquib('/Users/maor/Documents/pyquibbler/examples/compare_images/pipes.jpg')
image = plt.imread(file_name)

plt.figure(1)
plt.imshow(image, aspect="auto")


#
# Define ROIs
images_count = iquib(6)
images_count.set_assignment_template(0, 10, 1)
#
# roi_default = iquib([[10, 120, 50, 160]])
roi_default = iquib([[10, 110, 10, 110]])
roi_default.allow_overriding = False

rois = np.repeat(roi_default, images_count, axis=0)
rois.set_assignment_template(0, 1000, 1)
rois.allow_overriding = True

# Plot ROIs on main image:
for roi in rois.iter_first(images_count.get_value()):
    create_roi(roi, plt.gca())

cut_images_lst = [cut_image(roi) for roi in rois.iter_first(images_count.get_value())]


# Plot images
fig = plt.figure(2)
grid = ImageGrid(fig, 111,  # similar to subplot(111)
                 nrows_ncols=(3, 3),  # creates 2x2 grid of axes
                 axes_pad=0.1,  # pad between axes in inch.
                 )

for ax, im in zip(grid, cut_images_lst):
    # Iterating over the grid returns the Axes.
    ax.imshow(im)


# Compare sub images
image_distances = np.array([image_distance(img1, img2) for img1, img2 in zip(cut_images_lst, cut_images_lst)])
threshold = iquib(.1)
is_adjacent = image_distances < threshold


# Plot distance matrix
plt.figure(3)
plt.axis([0.5, images_count+0.5, 0.5, images_count+0.5 ])
plt.title('pairwise distance between images')
plt.xlabel('Image number')
plt.ylabel('Image number')
#
# for i in range(images_count.get_value()):
#     plt.plot(list(range(images_count.get_value())), 'rx', markersize=np.array([10, 0, 0, 10, 0, 10]), linewidth=3)

# arrayfun(@plot,gca,1:nImages,(1:nImages)',"rx","markersize",isAdjacent.*18+1,"linewidth",3 ,EvalNow);

#
# for distances in image_distances.iter_first(images_count.get_value()):
#     plt.imshow(image_distances[0])
# imagesc(dist)
# colormap gray
# hold on
# arrayfun(@plot,gca,1:nImages,(1:nImages)',"rx","markersize",isAdjacent.*18+1,"linewidth",3 ,EvalNow);
# caxis([0 1])
# axis([0.5 nImages+0.5 0.5 nImages+0.5 ])
# axis square
# title('pairwise distance between images')
# xlabel('Image number')
# ylabel('Image number')
# set(gca,'FontSize',18)


"""

a = [[...], [...]]
r = Rec(a[0])
g = r.extents[0]
del r


"""


plt.show(block=True)
# ROIs = repmat(ROIdefault,nImages,1, 'AssignmentTemplate',{[0 1000 1]}, 'AssignmentPermission','open');
#
# % Plot ROIs on main image:
# EvalNow = quibProps('EvaluateNow',true);
# cellfun(@images_roi_Rectangle,{gca},{'Position'},ROIs,{'FaceSelectable'},{false},{'color'},{'k'}, EvalNow);
#
# % Cut sub-images by ROIs
# cutImgs = cellfun(@cutimage, {Img}, ROIs,'UniformOutput',false, quibProps('Cache','on'));
#
# % prepare axes to plot images
# figure(2);clf
# axs = tight_subplot(2,3);
# arrayfun(@(a)hold(a,'on'),axs);
# set(axs,'YDir','reverse')
# axis(axs,'equal')
# nPlot = min(numel(axs),nImages);
# caxs = feval(@(n)num2cell(axs(1:n)),nPlot);
# allaxis = cellfun(@(ax,roi) qblr_functions.axis(ax,[0 roi(3) 0 roi(4)]),caxs,ROIs(1:nPlot),EvalNow);
#
# % plot images:
# allimgs = cellfun(@(ax,im) image(ax,im),caxs,cutImgs(1:nPlot),EvalNow);
#
# % Compare sub-images
# dist = cellfun(@compareimagepairs,cutImgs,cutImgs');
# Threshold = iquib(0.1);
# isAdjacent = dist<Threshold;
# comp = feval(@(d) conncomp(graph(d))', isAdjacent);
#
# % Plot distance matrix
# figure(3); clf
# imagesc(dist)
# colormap gray
# hold on
# arrayfun(@plot,gca,1:nImages,(1:nImages)',"rx","markersize",isAdjacent.*18+1,"linewidth",3 ,EvalNow);
# caxis([0 1])
# axis([0.5 nImages+0.5 0.5 nImages+0.5 ])
# axis square
# title('pairwise distance between images')
# xlabel('Image number')
# ylabel('Image number')
# set(gca,'FontSize',18)
#
# y = linspace(0,1,21);
# axes('Position',[0.9 0.2 0.05 0.6])
# imagesc(0,y',y')
# ylim([0 1])
# set(gca,'YDir','normal','XTick',[],'FontSize',14)
# line(gca,'xdata',0.5,'YData',Threshold,'marker','<',...
# 'markerfacecolor','r','markersize',30)
# ylabel('Similarity Threshold')
#
# % Add classification group to image:
# figure(1)
# cellfun(@(roi,grp) text(gca,double(roi(1)+roi(3)/2),double(roi(2)+roi(4)/2),char('A'+grp-1), ...
# "fontsize",26,"verticalalignment","middle","horizontalalignment","center"),ROIs,num2cell(comp), ...
# EvalNow);
#
# % Add UIContol for Number of images:
# uicontrol(gcf,'Style','slider','Min',1,'Max',7,'Value',nImages,'Position',[10 10 200 20])
# uicontrol(gcf,'Style','text','String',sprintf('Number of images = %d',nImages),'Position',[10 30 200 15])
#
# % Add UIContol for Similarity threshold:
# uicontrol(gcf,'Style','slider','Max',1,'Value',Threshold,'Position',[10 60 200 20])
# uicontrol(gcf,'Style','text','String',sprintf('Similarity threshold = %4.2f',Threshold),'Position',[10 80 200 15])
#
#
# function dist = compareimagepairs(img1,img2)
# fprintf('Comparing two ROI images...\n')
# rgb1 = mean(img1,[1 2]);
# rgb2 = mean(img2,[1 2]);
# dist = 1 - corr(rgb1(:),rgb2(:));
# end
#
# function cutimg = cutimage(img,roi)
# fprintf('\nCutting a single ROI image...\n')
# cutimg = img(roi(2)+(0:roi(4)), roi(1)+(0:roi(3)),:);
# end