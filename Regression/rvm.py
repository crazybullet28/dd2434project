
import numpy as np
from math import *
import random
import math
from sklearn import datasets
from sklearn import svm
import matplotlib.pyplot as plt
from cvxopt.solvers import qp
from cvxopt.base import matrix


convThreshold = 0.00000001
alphaThreshold = 10
relAlphaVal = 10
relAlphaValNoisa = 150



class DataSets:
    def __init__(self):
        pass


    def genFriedman(self, i=1, N=240, D=10):
        if i not in range(1,4):
            raise Exception('not a correct dataset')

        if i == 1:
            X, Y = datasets.make_friedman1(N, D )

        if i == 2:
            X, Y = datasets.make_friedman2(N, D)

        if i == 3:
            X, Y = datasets.make_friedman3(N, D)
        return X, Y




def generateData(noise = 0, N = 100):
    xini = np.linspace(-10, 10, N)
    xinp = map(lambda x:[x] , xini)

    # xinp = xini.reshape(1,100)
    finp = (1/abs(xini)) * np.sin(np.abs(xini))
    if noise == 1:
        finp = noisify(finp, 'uniform')
    if noise == 2:
        finp = noisify(finp, 'gaussian')
    print xinp
    print finp.shape

    return xinp, finp


def noisify(yinp, type='uniform'):
    finp = yinp
    if type == 'uniform':
        noise = np.random.uniform(-0.2, 0.2, len(yinp))
    if type == 'gaussian':
        noise = np.random.normal(0, 0.2, 100)
    finp = finp + noise
    return finp


def rmse(xo, xp):
    val = sqrt(sum([(x-y) ** 2 for x,y in zip(xo,xp)]))
    return val


def kernel(x, y, type='l'):
    r = 0.5
    if type == 'l':
        val = sum([p*q  for p,q in zip(x, y)]) + 1
    if type == 'sq':
        val =  (sum([p*q  for p,q in zip(x, y)]) + 1) ** 2
    if type == 'c':
        val =  (sum([p*q  for p,q in zip(x, y)]) + 1) ** 3
    if type == 'linspline':
        val = reduce(lambda x,y: x*y, [(p*q + 1 + p*q*min(p,q) - ((p+q)/2) * min(p,q) ** 2 + (min(p,q) ** 3)/3) for p,q in zip(x,y) ])
        # val = reduce(lambda x,y: x*y, [(p*q + 1 + min(p,q)) for p,q in zip(x,y)])
    if type == 'gaussian':
        val = math.exp(-(r**(-2)*(x[0]-y[0])**2))
    return val

def splineKernel(x):
    kerMat = np.ones((len(x), len(x)))
    for i in range(len(x)):
        for j in range(len(x)):
            # kerMat[i,j] = sum([p*q + 1 + p*q*min(p,q) - (float(p+q)/2) * float(min(p,q)) ** 2 + float(min(p,q) ** 3)/3 for p,q in zip(x[i], x[j])])
            # kerMat[i,j] = reduce(lambda x,y: x*y, [p*q + 1 + p*q*min(p,q) - (float(p+q)/2) * float(min(p,q)) ** 2 + float(min(p,q) ** 3)/3 for p,q in zip(x[i], x[j])])
            # kerMat[i,j] = reduce(lambda x,y: x*y, [p*q + 1 + p*q*min(p,q) - (float(p+q)/2) * (float(min(p,q)) ** 2 + (min(p,q) ** 3)/3)  for p,q in zip(x[i], x[j])] )
            kerMat[i,j] = reduce(lambda x,y: x*y, [p*q + 1 + min(p,q)  for p,q in zip(x[i], x[j])] )
            # kerMat[i,j] = (sum([p*q  for p,q in zip(x[i], x[j])]) + 1) ** 2
    print kerMat
    return kerMat


def tuneSVMparams():
    pass



def getDesMat(xinp):
    desMat = np.ones((len(xinp), len(xinp) + 1))
    for i in range(len(xinp)):
        desMat[i,0] = 1
        for j in range(len(xinp)):
            desMat[i,j+1] = kernel(xinp[i], xinp[j], 'linspline')
    return desMat



def predictRVM(xtest, xinp, muMat):
    yest = np.ones(len(xtest))

    for i in range(len(xtest)):
        xkernel = np.ones(len(xinp) + 1)
        xkernel[0] = 1
        for j in range(len(xinp)):
            xkernel[j+1] = kernel(xtest[i], xinp[j], 'linspline')
        yest[i] =  np.dot(np.transpose(muMat),xkernel)

    xplot, yplot = generateData(noise=0, N=100)
    plt.plot(xplot, yplot, marker = '+', c='y')

    plt.scatter(xtest, yest, marker = '^', s = 70, c='green')
    # plt.savefig('rvm-sinc-0noise-estimate.png')
    plt.show()

    return yest


def rvmtrain(xinp, yinp, beta = 1):

    dmat = getDesMat(xinp)
    N = len(yinp)
    print dmat.shape
    target = yinp
    alphas = np.ones((len(xinp) +1, 1))/float(N**2)
    Amat = np.diagflat(alphas)
    newAlphas = alphas

    convAlphasInd = []

    for t in range(300):
        sig = Amat + beta * np.dot(dmat.transpose(), dmat)
        sigMat = np.linalg.inv(sig)
        mMat = beta * np.dot(sigMat, np.dot(dmat.transpose(), target))

        print mMat.shape
        print sigMat.shape
        # print alphas
        print Amat.shape
        gammasum = 0
        oldAlphas = np.ones((len(newAlphas),1))
        for i in range(len(newAlphas)):
            gammasum += (1 - newAlphas[i] * sigMat[i,i])

            if i in convAlphasInd:
                continue

            print oldAlphas[i,0]
            print mMat[i]
            if float(mMat[i] ** 2) == 0 :
                newAlphas[i] = 1000000
            else:
                oldAlphas[i] = newAlphas[i]
                newAlphas[i,0] = (1 - newAlphas[i,0] * sigMat[i,i]) / float(mMat[i] **2)
            print oldAlphas[i,0]
            print newAlphas[i,0]

            if np.abs(oldAlphas[i,0] - newAlphas[i,0]) < convThreshold:
                convAlphasInd.append(i)


        # exit()


        for i in range(len(newAlphas)):
            redIndex = []
            if newAlphas[i] > alphaThreshold:
                redIndex.append(i)

        redIndex.sort(reverse=True)


        # code to sparsify the matrices, removing the irrelevant alphas
        # newAlphas = np.delete(newAlphas, redIndex, 0)
        # dmat = np.delete(dmat, redIndex, 1)
        print newAlphas.shape
        print dmat.shape

        beta = ( N - gammasum) / float(np.linalg.norm(target - np.dot(dmat, mMat)))

        print 'beta'
        print beta
        Amat = np.diagflat(newAlphas)

    # support_vecs = list(newAlphas < 1000000)
    relevant_vecs_ind = []
    x_rel =[]
    y_rel = []

    for i in range(N +1):
        if newAlphas[i] < relAlphaVal:
            relevant_vecs_ind.append(i+1)
            x_rel.append(xinp[i-1])
            y_rel.append(yinp[i-1])

    print relevant_vecs_ind
    print len(relevant_vecs_ind)
    print x_rel
    print y_rel
    plt.ylim((-0.4, 1.2))
    plt.xlim((-11, 11))
    plt.scatter(zip(*x_rel), y_rel, marker = 'o', c='r', s=50)
    plt.plot(xinp, yinp, marker = '^', c= 'b')
    plt.savefig('rvm-sinc-1noise.png')
    # print support_vecs
    # print zip(*(newAlphas < 10000))
    # xrel = xinp[zip(*(newAlphas < 10000))]
    # yrel = yinp[newAlphas < 10000]
    # print dmat
    # plt.show()
    # exit()
    muMat = mMat
    return muMat



def svmtrain(xinp, yinp):


    pass


def main():
    ds  = DataSets()
    xinp, yinp=  ds.genFriedman(1)
    xinp, yinp = generateData(noise = 2, N = 100)
    xplot, yplot = generateData(noise=0, N = 100)
    splKernel = splineKernel(xinp)
    svr_rbf  = svm.SVR(C = 1, epsilon = 0.05, kernel = 'rbf')
    svr_spline  = svm.SVR(C = 10, epsilon = 0.02, kernel = 'precomputed')
    print type(yinp)
    yinp = list(yinp)
    print splKernel.shape
    beta = 100
    # print yinp.shape
    # exit()
    muMat = rvmtrain(xinp, yinp, beta)
    y_rvm_est = predictRVM(xinp, xinp, muMat)
    err_rvm = rmse(yinp, y_rvm_est)
    print 'rvm error'
    print err_rvm
    svr_rbf.fit(xinp, yinp)
    svr_spline.fit(splKernel, yinp)

    # x_min, x_max = xinp[:].min() - 1, xinp[:].max() + 1
    # y_min, y_max = yinp[:].min() - 1, xinp[:].max() + 1
    # xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
    # Z = svr_rbf.predict(np.c_[xx.ravel(), yy.ravel()])


    # Z = Z.reshape(xx.shape)
    # plt.pcolormesh(xx, yy, Z, cmap=plt.cm.Paired)
    yest = svr_rbf.predict(xinp)
    yspest = svr_spline.predict(splKernel)
    err_rbf = rmse(yinp, yest)
    err_spline = rmse(yinp, yspest)
    # rvm1 = rvmtrain(xinp, yinp)

    print err_rbf
    print err_spline

    plt.ylim((-0.4, 1.2))
    plt.xlim((-11, 11))
    print svr_rbf
    print svr_rbf.support_
    xinp_support = [xinp[i] for i in svr_spline.support_]
    yinp_support = [yinp[i] for i in svr_spline.support_]
    print yinp_support
    print xinp_support
    # print x
    print len(svr_rbf.support_vectors_)
    plt.scatter(xinp_support, yinp_support, marker = 'o', c='r', alpha=1, s=60)
    plt.plot(xinp, yinp, marker = '^', c= 'b')
    plt.plot(xplot, yplot, marker = '+', c='y')
    # plt.plot(xinp, yest, marker = '^', c= 'r')
    # plt.plot(xinp, yspest, marker = '^', c= 'r')
    # plt.plot()
    plt.show()
    # plt.savefig('svm-rbf2.png')



if __name__ == '__main__':
    main()


